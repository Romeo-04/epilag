"""Rasterise the province and region maps into voxel grids for the 3D pixel maps (site/public/geo/*.json).

Each grid cell holds the index of the area whose polygon contains the cell centre (or -1 for sea), using the same
equirectangular projection as scripts/drill_data.py (longitude scaled by cos(mean latitude)). Small islands that no
cell centre falls in still get the cell under their centroid, so every area appears on the map.
Rows are run-length encoded as [area, run, area, run, ...].

Outputs:
  voxel_ph.json       national grids: provinces and regions, fine (0.05 deg) and coarse (0.08 deg, for phones)
  voxel_regions.json  one board per region (its provinces only, about 72 cells on the long side) for Dengue Drill
Usage: python scripts/voxel_data.py   (needs numpy only)
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "data"
OUT = ROOT / "site" / "public" / "geo"
QC = {"unit_id": "QC", "lon": 121.0437, "lat": 14.6760}  # Quezon City has no polygon in region.geojson


def rings_of(feature):
    g = feature["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [np.asarray(r, dtype=float) for poly in polys for r in poly]


def inside(px, py, rings):
    """Even-odd point-in-polygon for many points against all rings (outer rings and holes)."""
    hit = np.zeros(px.shape, dtype=bool)
    for r in rings:
        x0, y0 = r[:, 0], r[:, 1]
        x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
        for a, b, c, d in zip(x0, y0, x1, y1):
            if b == d:
                continue
            cross = (b > py) != (d > py)
            xi = a + (py - b) * (c - a) / (d - b)
            hit ^= cross & (px < xi)
    return hit


def rasterise(features, cell, lat0=None, pad=1):
    """Grid of area indices for these features. `cell` is the cell height in degrees of latitude."""
    allr = [rings_of(f) for f in features]
    pts = np.concatenate([r for rs in allr for r in rs])
    lat0 = float(pts[:, 1].mean()) if lat0 is None else lat0
    kx = math.cos(math.radians(lat0))
    lon0, lon1 = pts[:, 0].min(), pts[:, 0].max()
    lat_lo, lat_hi = pts[:, 1].min(), pts[:, 1].max()
    cellx = cell / kx  # same ground width as height
    w = int(math.ceil((lon1 - lon0) / cellx)) + 2 * pad
    h = int(math.ceil((lat_hi - lat_lo) / cell)) + 2 * pad
    ox, oy = lon0 - pad * cellx, lat_hi + pad * cell  # top-left corner (north-west)
    gx, gy = np.meshgrid(ox + (np.arange(w) + 0.5) * cellx, oy - (np.arange(h) + 0.5) * cell)
    grid = np.full((h, w), -1, dtype=np.int16)
    for i, rs in enumerate(allr):
        rp = np.concatenate(rs)
        m = (gx >= rp[:, 0].min()) & (gx <= rp[:, 0].max()) & (gy >= rp[:, 1].min()) & (gy <= rp[:, 1].max()) & (grid < 0)
        if m.any():
            sel = inside(gx[m], gy[m], rs)
            idx = np.flatnonzero(m)[sel]
            grid.flat[idx] = i
        if not (grid == i).any():  # too small for any cell centre: take the cell under the centroid of its largest ring
            big = max(rs, key=len)
            cx, cy = big[:, 0].mean(), big[:, 1].mean()
            col, row = int((cx - ox) / cellx), int((oy - cy) / cell)
            if 0 <= row < h and 0 <= col < w:
                grid[row, col] = i
    meta = {"cell": cell, "cellx": round(cellx, 6), "lat0": round(lat0, 4), "origin": [round(ox, 5), round(oy, 5)], "w": w, "h": h}
    return grid, meta


def rle(grid):
    out = []
    for row in grid:
        r, prev, run = [], int(row[0]), 0
        for v in row:
            v = int(v)
            if v == prev:
                run += 1
            else:
                r += [prev, run]
                prev, run = v, 1
        out.append(r + [prev, run])
    return out


def cell_of(meta, lon, lat):
    return [int((lon - meta["origin"][0]) / meta["cellx"]), int((meta["origin"][1] - lat) / meta["cell"])]


def pack(features, cell, lat0=None):
    grid, meta = rasterise(features, cell, lat0)
    counts = np.bincount(grid[grid >= 0].ravel(), minlength=len(features))
    return {**meta, "units": [f["properties"]["unit_id"] for f in features], "cells": counts.tolist(), "rows": rle(grid)}, grid


def main():
    prov = json.loads((DATA / "province.geojson").read_text())["features"]
    reg = json.loads((DATA / "region.geojson").read_text())["features"]
    OUT.mkdir(parents=True, exist_ok=True)

    national = {}
    for key, feats, cell in [("province", prov, 0.05), ("region", reg, 0.05), ("province_coarse", prov, 0.08), ("region_coarse", reg, 0.08)]:
        g, grid = pack(feats, cell)
        if key.startswith("region"):
            g["markers"] = {QC["unit_id"]: cell_of(g, QC["lon"], QC["lat"])}
        national[key] = g
        land = int((grid >= 0).sum())
        print(f"{key:16s} {g['w']}x{g['h']} cells, {land} land, smallest area {min(g['cells'])} cells")
    (OUT / "voxel_ph.json").write_text(json.dumps(national, separators=(",", ":")))

    # one board per Dengue Drill region (its provinces, as listed in site/public/drill/data.json), long side about 72 cells
    drill = json.loads((ROOT / "site" / "public" / "drill" / "data.json").read_text())
    by_id = {f["properties"]["unit_id"]: f for f in prov}
    boards = {}
    for region in drill["regions"]:
        feats = [by_id[p["id"]] for p in region["provinces"] if p["id"] in by_id]
        rid = region["id"]
        pts = np.concatenate([r for f in feats for r in rings_of(f)])
        kx = math.cos(math.radians(pts[:, 1].mean()))
        span = max((pts[:, 0].max() - pts[:, 0].min()) * kx, pts[:, 1].max() - pts[:, 1].min())
        g, _ = pack(feats, span / 72)
        boards[rid] = g
    (OUT / "voxel_regions.json").write_text(json.dumps(boards, separators=(",", ":")))
    for p in sorted(OUT.glob("voxel_*.json")):
        print(f"{p.relative_to(ROOT)}: {p.stat().st_size / 1e3:.0f} kB")
    print(f"{len(boards)} region boards")


if __name__ == "__main__":
    main()
