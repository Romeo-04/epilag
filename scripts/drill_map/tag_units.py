"""Tag each PSGC province polygon with its EpiLag forecast unit and region (used by boundaries.sh).

The boundary set uses today's regions; the forecast units use the older ones, so:
- Negros Island Region provinces go back to the region listed for them in docs/web/data/meta.json (VI, VII)
- Maguindanao del Norte and del Sur (087, 088) merge into MAG, "Maguindanao (pre-2022)"
- City of Isabela (901) is the unit PH09097
- Quezon City (boundaries.sh gives it the code 813, its own PSGC) is the unit QC, cut out of the Second District
- the Special Geographic Area (999) has no forecast unit and stays in BARMM as X_SGA
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
meta = json.loads((ROOT / "docs/web/data/meta.json").read_text())
units = meta["panels"]["province"]["units"]
by_code = {u[-3:]: u for u in units if u.startswith("PH")}
region_of = {p: r["id"] for r in meta["regions"] for p in r["provinces"]}
special = {"087": ("MAG", "R_BARMM"), "088": ("MAG", "R_BARMM"), "901": ("PH09097", "R_REGION_IX"), "999": ("X_SGA", "R_BARMM"), "813": ("QC", "R_NCR")}

src, dest = sys.argv[1], sys.argv[2]
geo = json.loads(Path(src).read_text())
for f in geo["features"]:
    psgc = f["properties"]["adm2_psgc"]
    code = "%03d" % ((psgc // 100000) % 1000)
    unit, region = special.get(code) or (by_code.get(code), region_of.get(by_code.get(code)))
    if not unit or not region:
        sys.exit(f"no forecast unit for PSGC {psgc}")
    f["properties"] = {"unit": unit, "region": region, "psgc": psgc}
missing = set(units) - {f["properties"]["unit"] for f in geo["features"]}
if missing:
    sys.exit(f"forecast units with no boundary: {sorted(missing)}")
Path(dest).write_text(json.dumps(geo))
