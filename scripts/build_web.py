"""Export the data and copy for the JavaScript web app (site/web/ -> docs/web/).

Writes compact JSON into site/public/web/data/, which Vite copies to docs/web/data/:
  meta.json                       units, names, populations and data dates per panel, and the regions with their
                                  provinces and cities (for the Region -> Province / City pickers)
  {panel}_forecast.json           latest forecasts (2/4/6/8 weeks ahead)
  {panel}_thresholds.json         alert / epidemic thresholds per unit and week of year
  {panel}_history.json            weekly reported cases
  {panel}_backtest.json           out-of-sample forecasts (replay mode, unit chart)
  {panel}_drivers.json            SHAP contributions per unit and horizon ("why this forecast")
  qc_barangays.json               Quezon City barangay shares
  reports.json                    backtest and early-warning summaries ("Did it work?")
  i18n.json                       EN/FIL copy, read from app/streamlit_app.py so both apps say the same thing

Tables are columnar: {"n": rows, "cols": {name: [values]}}. Unit ids become indexes into meta.units[panel],
dates become days since 1970-01-01, and floats are rounded to 4 significant digits (as the old in-browser
build's CSV export did). Usage: python scripts/build_web.py
"""
import ast
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "data"
REPORTS = ROOT / "reports"
OUT = ROOT / "site" / "public" / "web" / "data"
I18N = ROOT / "site" / "src" / "app" / "i18n.json"
PANELS = ["region_qc", "province"]
# Dengue Drill region codes (PSGC) -> region unit ids of the region_qc panel
REGION_OF = {"PH01": "R_REGION_I", "PH02": "R_REGION_II", "PH03": "R_REGION_III", "PH04": "R_REGION_IV-A",
             "PH05": "R_REGION_V", "PH06": "R_REGION_VI", "PH07": "R_REGION_VII", "PH08": "R_REGION_VIII",
             "PH09": "R_REGION_IX", "PH10": "R_REGION_X", "PH11": "R_REGION_XI", "PH12": "R_REGION_XII",
             "PH13": "R_NCR", "PH14": "R_CAR", "PH16": "R_REGION_XIII", "PH17": "R_MIMAROPA", "PH19": "R_BARMM"}
CITIES = {"R_NCR": ["QC"]}  # cities with their own (latest) forecast, listed under their region
EPOCH = pd.Timestamp("1970-01-01")


def g4(x):
    """Round to 4 significant digits; None for missing."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, float):
        r = float(f"{x:.4g}")
        return int(r) if r.is_integer() else r
    return x


def table(df: pd.DataFrame, units: list[str]) -> dict:
    index = {u: i for i, u in enumerate(units)}
    cols = {}
    for c in df.columns:
        s = df[c]
        if c == "unit_id":
            cols["u"] = [index[u] for u in s]
        elif c == "unit_name":
            continue  # in meta
        elif pd.api.types.is_datetime64_any_dtype(s):
            cols[c] = [int((d - EPOCH).days) for d in s]
        elif pd.api.types.is_float_dtype(s):
            cols[c] = [g4(float(v)) for v in s]
        elif pd.api.types.is_integer_dtype(s):
            cols[c] = [int(v) for v in s]
        else:
            cols[c] = [None if pd.isna(v) else str(v) for v in s]
    return {"n": len(df), "cols": cols}


def write(name: str, obj) -> None:
    path = OUT / name
    path.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {path.stat().st_size / 1e3:.0f} kB")


def i18n() -> dict:
    """The copy dictionaries of app/streamlit_app.py, read without importing Streamlit."""
    tree = ast.parse((ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            found[node.targets[0].id] = node.value
    out = {name: ast.literal_eval(found[name]) for name in ("PANELS", "T", "ALERT_TEXT", "PLAYBOOK", "FEATURES", "PUBLIC")}
    levels = ast.literal_eval(found["LEVELS"])
    out["LEVELS"] = levels
    out["LEVEL_NAME"] = eval(compile(ast.Expression(found["LEVEL_NAME"]), "LEVEL_NAME", "eval"),  # noqa: S307
                             {"__builtins__": {}}, {"dict": dict, "zip": zip, "LEVELS": levels})
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"panels": {}}
    for panel in PANELS:
        fc = pd.read_parquet(DATA / f"{panel}_forecast.parquet")
        hist = pd.read_parquet(DATA / f"{panel}_history.parquet")
        names = pd.concat([fc[["unit_id", "unit_name"]], hist[["unit_id", "unit_name"]]]).drop_duplicates("unit_id")
        units = sorted(names.unit_id)
        pop = fc.drop_duplicates("unit_id").set_index("unit_id").population
        meta["panels"][panel] = {
            "units": units,
            "names": dict(zip(names.unit_id, names.unit_name)),
            "population": {u: int(pop[u]) for u in units if u in pop.index},
            "forecast_week": str(fc.week.max().date()),
            "history_end": str(hist.week.max().date()),
        }
        write(f"{panel}_forecast.json", table(fc.drop(columns=["unit_name", "population"]), units))
        write(f"{panel}_thresholds.json", table(pd.read_parquet(DATA / f"{panel}_thresholds.parquet"), units))
        write(f"{panel}_history.json", table(hist[["unit_id", "week", "cases"]], units))
        write(f"{panel}_backtest.json", table(pd.read_parquet(DATA / f"{panel}_backtest.parquet"), units))
        write(f"{panel}_drivers.json", table(pd.read_parquet(DATA / f"{panel}_drivers.parquet"), units))
    # regions in PSGC order, each with its provinces (old panel, to Jan 2021) and cities (latest panel)
    drill = json.loads((ROOT / "site" / "public" / "drill" / "data.json").read_text(encoding="utf-8"))
    meta["regions"] = [{"id": REGION_OF[r["id"]], "psgc": r["id"], "name": r["name"],
                        "provinces": [p["id"] for p in r["provinces"]], "cities": CITIES.get(REGION_OF[r["id"]], [])}
                       for r in sorted(drill["regions"], key=lambda r: r["id"])]
    write("meta.json", meta)

    brgy = pd.read_csv(DATA / "qc_barangays.csv")
    write("qc_barangays.json", [{k: g4(v) if isinstance(v, float) else v for k, v in r.items()}
                                for r in brgy.to_dict("records")])

    reports = {}
    for panel in PANELS:
        reports[panel] = {}
        for name, f in {"backtest": f"backtest_{panel}.csv", "backtest_noweather": f"backtest_{panel}_noweather.csv",
                        "alerts": f"alerts_{panel}.csv"}.items():
            if (REPORTS / f).exists():
                reports[panel][name] = [{k: g4(v) if isinstance(v, float) else v for k, v in r.items()}
                                        for r in pd.read_csv(REPORTS / f).to_dict("records")]
    write("reports.json", reports)

    I18N.parent.mkdir(parents=True, exist_ok=True)
    I18N.write_text(json.dumps(i18n(), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{I18N.relative_to(ROOT)}: {I18N.stat().st_size / 1e3:.0f} kB")


if __name__ == "__main__":
    main()
