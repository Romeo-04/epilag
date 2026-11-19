// Names for the drill-down map (lib/drill-map.js), shared by the forecast map and the overview.
const CODES = { R_NCR: "NCR", R_CAR: "CAR", R_BARMM: "BARMM", R_MIMAROPA: "MIMAROPA" };
export const shortName = (s) => s.replace("Metropolitan Manila ", "Metro Manila ").replace(" District", "").replace(" (pre-2022)", "");

/** Region names for the map: full name, short name ("Cagayan Valley") and map tag ("II", "NCR"). */
export function regionNames(regions) {
  const out = {};
  for (const r of regions) {
    const m = /\(([^)]+)\)/.exec(r.name), inner = m ? m[1] : r.name;
    const code = CODES[r.id] || r.name.split(" (")[0];
    out[r.id] = { name: r.name, short: CODES[r.id] === "NCR" ? "NCR" : inner.replace(/ Region$/, ""), tag: CODES[r.id] || code.replace(/^Region /, ""), code };
  }
  return out;
}

/** Every name the map needs, from meta.json. */
export const drillNames = (m, special) => ({
  region: regionNames(m.regions || []),
  province: Object.fromEntries(Object.entries(m.panels.province.names).map(([k, v]) => [k, shortName(v)])),
  city: m.panels.region_qc.names.QC || "Quezon City", special,
});

/** Where the forecast map should open for a place picked on the map: URL settings for ctx.go("map", ...). */
export function mapTarget(node, panel) {
  if (!node) return { focus: null };
  const region = node.kind === "region" ? node.id : node.kind === "province" ? node.region : "R_NCR";
  if (panel === "province") return node.kind === "province" ? { focus: node.id, region, area: node.id } : { focus: node.id };
  return { focus: node.id, region, area: node.kind === "city" || node.kind === "barangay" ? "QC" : region };
}
