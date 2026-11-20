import json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from thresholds import thresholds
WEB = ROOT / "site/public/web/data"
units = json.load(open(WEB / "meta.json"))["panels"]["region_qc"]["units"]
def table(n):
    df = pd.DataFrame(json.load(open(WEB / n))["cols"]); df["unit_id"] = df.u.map(dict(enumerate(units))); return df
h = table("region_qc_history.json"); h["week"] = pd.to_datetime(h.week, unit="D")
qc = h[h.unit_id == "QC"][["week", "cases"]]
line = thresholds(qc.assign(unit_id="QC")[qc.week.dt.year < 2024])[["woy", "epidemic"]]
s = qc[qc.week.between("2024-08-04", "2025-06-29")].copy()
s["woy"] = s.week.dt.isocalendar().week.clip(upper=52).astype(int)
s = s.merge(line, on="woy").sort_values("week")
bt = table("region_qc_backtest.json"); print(bt.columns.tolist(), file=sys.stderr)
bt["target_week"] = pd.to_datetime(bt.target_week, unit="D")
b = bt[(bt.unit_id == "QC") & (bt.horizon == 4)]
out = {"weeks": [d.strftime("%Y-%m-%d") for d in s.week], "cases": s.cases.astype(int).tolist(), "epi": s.epidemic.round(1).tolist(),
       "above": int((s[s.week >= "2024-09-01"].cases > s[s.week >= "2024-09-01"].epidemic).sum())}
print(b[b.target_week.between("2024-09-01","2025-03-16")].head(3).to_string(), file=sys.stderr)
fc = b.set_index(b.target_week.dt.strftime("%Y-%m-%d")).q50
out["q50"] = [round(float(fc[w]),1) if w in fc.index else None for w in out["weeks"]]
json.dump(out, open(Path(__file__).parent / "qc.json", "w"))
print(out["above"], max(out["cases"]))
