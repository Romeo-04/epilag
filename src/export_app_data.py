"""Write the small files the Streamlit app reads (committed to the repo, so the app runs
without the raw data): boundaries, weekly history, 4-week-ahead backtest, QC barangay shares.

Boundaries: faeldon/philippines-json-maps (MIT), 2023 low-resolution GeoJSON.
"""
import json
from pathlib import Path

import pandas as pd
import requests

from features import PROC

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "app" / "data"
GEO = "https://raw.githubusercontent.com/faeldon/philippines-json-maps/master/2023/geojson"
REGION_PSGC = [100000000, 200000000, 300000000, 400000000, 500000000, 600000000, 700000000,
               800000000, 900000000, 1000000000, 1100000000, 1200000000, 1300000000,
               1400000000, 1600000000, 1700000000, 1900000000]
MAG_PARTS = {"PH19087", "PH19088", "PH19099"}


def psgc_to_unit(psgc: int) -> str:
    s = str(psgc).zfill(10)
    code = f"PH{s[:2]}{s[2:5]}"
    if code == "PH09901":  # City of Isabela uses a special PSGC; COD-AB code is PH09097
        return "PH09097"
    return "MAG" if code in MAG_PARTS else code


def merge_features(features: list[dict], unit_id: str) -> dict:
    polys = []
    for f in features:
        g = f["geometry"]
        polys += [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return {"type": "Feature", "id": unit_id, "properties": {"unit_id": unit_id},
            "geometry": {"type": "MultiPolygon", "coordinates": polys}}


def province_geojson() -> dict:
    by_unit: dict[str, list] = {}
    for psgc in REGION_PSGC:
        url = f"{GEO}/regions/lowres/provdists-region-{psgc}.0.001.json"
        for f in requests.get(url, timeout=60).json()["features"]:
            by_unit.setdefault(psgc_to_unit(f["properties"]["adm2_psgc"]), []).append(f)
    return {"type": "FeatureCollection", "features": [merge_features(fs, u) for u, fs in by_unit.items()]}


def region_geojson() -> dict:
    from features import _region_code
    fc = requests.get(f"{GEO}/country/lowres/country.0.001.json", timeout=60).json()
    feats = []
    for f in fc["features"]:
        unit_id = "R_" + _region_code(f["properties"]["adm1_en"]).replace(" ", "_")
        feats.append(merge_features([f], unit_id))
    return {"type": "FeatureCollection", "features": feats}


def history(panel: str) -> pd.DataFrame:
    t = pd.read_parquet(PROC / f"model_table_{panel}.parquet")
    return t[["unit_id", "unit_name", "week", "cases"]].dropna(subset=["cases"])


def backtest(panel: str) -> pd.DataFrame:
    b = pd.read_parquet(PROC / f"backtest_{panel}.parquet")
    return b[b.horizon.isin([4, 8])][["unit_id", "target_week", "horizon", "test_year", "actual", "q10", "q50", "q90"]]


def qc_barangays() -> pd.DataFrame:
    b = pd.read_csv(ROOT / "data" / "raw" / "upri_noah" / "QC_YearlyData-Barangay(CSV).csv", encoding="utf-8-sig")
    recent = [f"DC_{y}" for y in (2022, 2023, 2024, 2025)]
    b["cases_2022_2025"] = b[recent].sum(axis=1, min_count=1)
    b["share"] = b.cases_2022_2025 / b.cases_2022_2025.sum()
    b["cases_2025"] = b.DC_2025
    return b[["ADM4_PCODE", "Barangay", "cases_2022_2025", "cases_2025", "share"]].sort_values("share", ascending=False)


def main() -> None:
    APP_DATA.mkdir(parents=True, exist_ok=True)
    (APP_DATA / "province.geojson").write_text(json.dumps(province_geojson()))
    (APP_DATA / "region.geojson").write_text(json.dumps(region_geojson()))
    for panel in ("province", "region_qc"):
        history(panel).to_parquet(APP_DATA / f"{panel}_history.parquet", index=False)
        backtest(panel).to_parquet(APP_DATA / f"{panel}_backtest.parquet", index=False)
    qc_barangays().to_csv(APP_DATA / "qc_barangays.csv", index=False)
    for p in sorted(APP_DATA.iterdir()):
        print(f"{p.name:40s} {p.stat().st_size:>10,}")


if __name__ == "__main__":
    main()
