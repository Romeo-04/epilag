// D9 comparison prototype (REDESIGN_PLAN.md 14, Phase 5): the same voxel grid drawn with MapLibre GL's
// fill-extrusion layer instead of Three.js. Each land cell is a small square polygon, extruded by its area's
// level; no basemap tiles. Same API subset as createVoxelMap (units, setValues, highlight, dispose).
// Used only behind the app's hidden ?map=maplibre switch.
import { decode } from "./voxel.js";

const SEA = "#BFE2EC", LAND = "#C9CFC9";

export async function createMaplibreMap(el, { grid, markers = false, pitch = 45, bearing = -14, lift = 6000, onPick, onHover } = {}) {
  const [{ default: maplibregl }] = await Promise.all([import("maplibre-gl"), import("maplibre-gl/dist/maplibre-gl.css")]);
  const { cells, units } = decode(grid, { markers });
  const [ox, oy] = grid.origin, cx = grid.cellx, cy = grid.cell;
  const features = cells.map((c) => {
    const x0 = ox + c.x * cx, y0 = oy - c.y * cy;
    return { type: "Feature", properties: { u: c.u },
      geometry: { type: "Polygon", coordinates: [[[x0, y0], [x0 + cx, y0], [x0 + cx, y0 - cy], [x0, y0 - cy], [x0, y0]]] } };
  });
  const value = units.map(() => ({ color: LAND, height: 1 }));
  let hot = -1;
  const holder = Object.assign(document.createElement("div"), { style: "position:absolute;inset:0" });
  el.append(holder);
  const map = new maplibregl.Map({
    container: holder, attributionControl: false, pitch, bearing, maxPitch: 70, dragRotate: true,
    bounds: [[ox, oy - grid.h * cy], [ox + grid.w * cx, oy]], fitBoundsOptions: { padding: 20 },
    style: { version: 8, sources: { cells: { type: "geojson", data: { type: "FeatureCollection", features } } },
      layers: [{ id: "sea", type: "background", paint: { "background-color": SEA } },
        { id: "land", type: "fill-extrusion", source: "cells", paint: { "fill-extrusion-color": LAND, "fill-extrusion-height": lift, "fill-extrusion-opacity": 1 } }] },
  });
  await new Promise((r) => map.once("load", r));

  const match = (get) => ["match", ["get", "u"], ...units.flatMap((_, i) => [i, get(i)]), get(-1)];
  function paint() {
    map.setPaintProperty("land", "fill-extrusion-color", match((i) => (i < 0 ? LAND : value[i].color)));
    map.setPaintProperty("land", "fill-extrusion-height", match((i) => (i < 0 ? lift : (value[i].height + (i === hot ? 1 : 0)) * lift)));
  }
  const index = new Map(units.map((u, i) => [u, i]));
  const at = (e) => { const f = map.queryRenderedFeatures(e.point, { layers: ["land"] })[0]; return f ? units[f.properties.u] : null; };
  if (onHover) map.on("mousemove", (e) => onHover(at(e), e.originalEvent));
  if (onPick) map.on("click", (e) => onPick(at(e), e.originalEvent));

  return {
    units,
    setValues(values) { for (const [u, v] of Object.entries(values)) { const i = index.get(u); if (i != null) value[i] = { ...value[i], ...v }; } paint(); },
    highlight(u) { const i = u == null ? -1 : index.get(u) ?? -1; if (i !== hot) { hot = i; paint(); } },
    project() { return null; },
    render() { map.triggerRepaint(); },
    dispose() { map.remove(); holder.remove(); },
  };
}
