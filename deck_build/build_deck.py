"""Build the EpiLag-PH final-round deck (20 slides, 1920x1080) as one HTML file.

Run from the repo root:  python deck_build/build_deck.py
Output: docs/deck/final/index.html (+ assets/). Render with deck_build/render.py [--pdf].
Numbers are read from the repo here; external facts and their sources are listed in
research/writeup/deck_plan.md (on research-b) and in the References slide.
"""
import base64
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import segno

from annotations import overlay
from art import icon, laptop, lonlat_to_px, phone, voxel_map

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(__file__).parent
OUT = ROOT / "docs/deck/final"
(OUT / "assets").mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))
from backtest import PARAMS  # noqa: E402
from thresholds import thresholds  # noqa: E402

WEB = ROOT / "site/public/web/data"
RES = ROOT / "research/results"
for f in (BUILD / "assets").glob("*"):
    shutil.copy(f, OUT / "assets" / f.name)
HAS = lambda name: (OUT / "assets" / name).exists()  # noqa: E731

# ================================================================== data
units = json.load(open(WEB / "meta.json"))["panels"]["region_qc"]["units"]


def table(name):
    df = pd.DataFrame(json.load(open(WEB / name))["cols"])
    df["unit_id"] = df.u.map(dict(enumerate(units)))
    return df


h = table("region_qc_history.json")
h["week"] = pd.to_datetime(h.week, unit="D")
qc = h[h.unit_id == "QC"][["unit_id", "week", "cases"]]
season_line = thresholds(qc[qc.week.dt.year < 2024])[["woy", "epidemic"]]


def with_line(df, col):
    df = df.copy()
    df["woy"] = df[col].dt.isocalendar().week.clip(upper=52).astype(int)
    return df.merge(season_line, on="woy").sort_values(col).reset_index(drop=True)


qc_season = with_line(qc[qc.week.between("2024-09-01", "2025-06-29")], "week")
weeks_above = int((qc_season.cases > qc_season.epidemic).sum())
bt = table("region_qc_backtest.json")
bt["target_week"] = pd.to_datetime(bt.target_week, unit="D")
qcb = with_line(bt[(bt.unit_id == "QC") & (bt.horizon == 4) & bt.target_week.between("2024-08-25", "2025-03-16")], "target_week")

mc = pd.read_csv(RES / "model_comparison.csv")
four = ["lightgbm", "negbin", "random_forest", "sarimax"]
piv = mc[mc.model.isin(four)].pivot_table(index=["panel", "test_year", "horizon"], columns="model", values="mae")
wins = piv.idxmin(axis=1).value_counts().reindex(four).fillna(0).astype(int)
rel = (piv.div(piv.lightgbm, axis=0) - 1).groupby(level="horizon").median() * 100
m5 = mc[mc.model.isin(four + ["blend_all4"])]
warn = (m5.groupby("model").caught_warning.sum() / m5.groupby("model").onsets.sum() * 100).round().astype(int)
beat = m5.groupby("model").apply(lambda g: int((g.rel_mae_vs_persistence < 1).sum()), include_groups=False)
relp = m5.pivot_table(index=["panel", "test_year", "horizon"], columns="model", values="rel_mae_vs_persistence")

shap = pd.read_csv(RES / "shap_groups.csv")
shap_cur = shap[(shap.panel == "region_qc") & (shap.feature_set == "current")]
lags = pd.read_csv(RES / "shap_lags.csv")
rain_lag = lags[(lags.panel == "region_qc") & (lags.feature_set == "current") & (lags.horizon == 4) & (lags.variable == "rain")].sort_values("lag_weeks")
fg = pd.read_csv(RES / "feature_groups.csv")
pf = pd.read_csv(RES / "proposed_features.csv")
nat = pd.read_csv(ROOT / "research/analysis/out/f2_province_national_totals.csv").set_index("year").national_total
calib = pd.read_csv(RES / "extracts/calibration.csv")
bp = {p: pd.read_csv(ROOT / f"reports/backtest_{p}.csv") for p in ("province", "region_qc")}
replay = json.load(open(ROOT / "docs/data/replay_2019-06-02.json"))
claim = replay["claim"]["4"]
rep_units = replay["horizons"]["4"]["units"]
drivers = table("region_qc_drivers.json")
qc_drv = drivers[(drivers.unit_id == "QC") & (drivers.horizon == 4)].copy()
qc_drv["grp"] = qc_drv.driver.map(lambda d: "Rain" if d.startswith("rain") else {"recent cases": "Recent cases", "season": "Time of year", "population": "Population"}.get(d, d))
qc_drv = qc_drv.groupby("grp").shap.sum()

# ================================================================== helpers
LOGO = (ROOT / "docs/favicon.svg").read_text()
LOGO_URI = "data:image/svg+xml;base64," + base64.b64encode(LOGO.encode()).decode()
QR_URI = segno.make("https://epilag.vercel.app", error="m").svg_data_uri(scale=6, border=1, dark="#14211B", light="#FFFFFF")
TRACK = ["Problem", "Story", "Literature", "Data", "Model", "Results", "System", "Impact"]


def path(xs, ys):
    return "M" + " L".join(f"{a:.1f},{c:.1f}" for a, c in zip(xs, ys))


def top(cur):
    tr = "".join(f'<span class="{"on" if t == cur else ""}">{t}</span>' for t in TRACK) if cur else ""
    return f'<div class="top"><span class="brand"><img src="{LOGO_URI}" alt=""><span>EpiLag<b>-PH</b></span></span><span class="track">{tr}</span></div>'


def foot(n, src=""):
    return f'<div class="foot"><span>{src}</span><span>{n}</span></div>'


def slide(n, section, heading, sub, body, src="", cls=""):
    return f'<section class="slide {cls}">{top(section)}<h1>{heading}</h1><h2>{sub}</h2>{body}{overlay(n)}{foot(n, src)}</section>'


def note(text, x, y, w=320, rot=-2, cls=""):
    return f'<div class="note {cls}" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg)">{text}</div>'


RIBBON = [("rain", "Rain"), ("container", "Breeding"), ("mosquito", "Bites"), ("sick", "Sickness"), ("counted", "Counted")]


def ribbon(size=84, labels=True, color="var(--ink)", hot_last=True):
    out = ""
    for i, (ic, lab) in enumerate(RIBBON):
        last = i == len(RIBBON) - 1
        out += f'<div class="rb{" hot" if (last and hot_last) else ""}">{icon(ic, size, color)}{f"<b>{lab}</b>" if labels else ""}</div>'
        if not last:
            out += '<div class="rbline"></div>'
    return f'<div class="ribbon">{out}</div>'


S = []

# ================================================================== 1 Hook
arrow1 = '<svg class="hookarrow" viewBox="0 0 380 360" width="380" height="360"><path d="M40 340 C 70 250, 150 150, 300 60" fill="none" stroke="#FF5A4E" stroke-width="6" stroke-linecap="round"/><path d="M266 52 L304 56 L292 92" fill="none" stroke="#FF5A4E" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
S.append(f"""<section class="slide dark hook"><img class="bleed" src="assets/bottlecap.jpg" alt="Aedes aegypti larvae in a bottle cap"><div class="shade"></div>{top(None)}
{arrow1}<div class="hooktext"><p class="l1"><em>Aedes aegypti</em> breeds in <span class="red">this much</span> water.</p>
<p class="l2">No specific treatment exists. Prevention means covering, emptying and cleaning water containers every week.</p></div>
<div class="foot"><span>Photo: CDC Public Health Image Library #26033 (Bishop, 2022). WHO (2025).</span><span>1</span></div></section>""")

# ================================================================== 2 Common
figs = "".join(f'<svg viewBox="0 0 60 100" class="fig {"hot" if k < 8 else ""}"><circle cx="30" cy="17" r="14"/><path d="M8 100 L8 56 Q8 36 30 36 Q52 36 52 56 L52 100 Z"/></svg>' for k in range(10))
S.append(f"""<section class="slide dark">{top(None)}
<h1 class="statement">Common shouldn't mean <span class="red">acceptable</span>.</h1>
<div class="two two3">
 <div><div class="huge">{nat.loc[2019]:,}</div><div class="say">dengue cases reported in 2019,<br>the year a national epidemic was declared</div></div>
 <div><div class="figs">{figs}</div><div class="huge red">8 in 10</div><div class="say">Quezon City residents who died of dengue<br>in early 2025 were minors</div></div>
</div>{overlay(2, True)}
<div class="foot"><span>DOH Epidemiology Bureau via HDX, 86 provinces. Andrade (2019). Sampang (2025).</span><span>2</span></div></section>""")

# ================================================================== 3 Problem (dark)
W, H, L, R, T, B = 1728, 330, 60, 20, 20, 46
x0, x1 = qc_season.week.min(), qc_season.week.max()
X = lambda d: L + (pd.Timestamp(d) - x0) / (x1 - x0) * (W - L - R)  # noqa: E731
Y = lambda v: T + (1 - v / 700) * (H - T - B)  # noqa: E731
bw = (W - L - R) / len(qc_season) * 0.72
bars = "".join(f'<rect x="{X(r.week)-bw/2:.1f}" y="{Y(r.cases):.1f}" width="{bw:.1f}" height="{Y(0)-Y(r.cases):.1f}" rx="3" fill="{"var(--red)" if r.cases > r.epidemic else "var(--dim)"}"/>' for r in qc_season.itertuples())
lineq = path([X(d) for d in qc_season.week], [Y(v) for v in qc_season.epidemic])
pk = qc_season.loc[qc_season.cases.idxmax()]
mon = "".join(f'<text x="{X(m):.1f}" y="{H-10}" class="tick" text-anchor="middle">{m.strftime("%b")}</text>' for m in pd.date_range("2024-09-01", "2025-06-01", freq="MS"))
xd = X("2025-02-15")
svg3 = f'''<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">{bars}<path d="{lineq}" fill="none" stroke="var(--ink)" stroke-width="2" stroke-dasharray="8 6" opacity=".7"/>{mon}
<line x1="{xd:.1f}" x2="{xd:.1f}" y1="{T}" y2="{H-B}" stroke="var(--ink)" stroke-width="2" opacity=".6"/>
<text x="{xd-12:.1f}" y="{T+24}" class="mk" text-anchor="end">Outbreak declared</text><text x="{xd-12:.1f}" y="{T+50}" class="mks" text-anchor="end">15 Feb 2025, five months in</text>
<text x="{X(pk.week)+16:.1f}" y="{Y(pk.cases)+20:.1f}" class="mk">{int(pk.cases)} cases</text><text x="{X(pk.week)+16:.1f}" y="{Y(pk.cases)+46:.1f}" class="mks">peak week</text></svg>'''
bg3 = '<img class="bleed dim" src="assets/problem.jpg">' if HAS("problem.jpg") else ""
S.append(f'''<section class="slide dark">{bg3}{top("Problem")}
<h1>The Problem</h1><h2>By the time a case is counted, the outbreak has already begun.</h2>
{ribbon(80, True, "var(--ink)")}
<div class="unused"><span>weeks of warning, unused</span></div>
<div class="cap3"><b class="red">{weeks_above} weeks</b> above the epidemic line in Quezon City, 2024 to 2025
<span class="leg"><i class="sw red"></i>week above the line<i class="sw dash"></i>epidemic line</span></div>
{svg3}
<div class="foot"><span>Quezon City weekly reported cases (Pelitro, 2026). Epidemic line: mean + 2 SD of the same weeks in earlier years. Declaration: Sampang (2025).</span><span>3</span></div></section>''')

# ================================================================== 4 Story (dark)
bg4 = '<img class="half right" src="assets/story.jpg">' if HAS("story.jpg") else ""
S.append(f"""<section class="slide dark story-slide">{bg4}{top("Story")}
<h1 class="logotitle"><img src="{LOGO_URI}" alt="">EpiLag<b>-PH</b></h1><h2>Who we are, and why we built it.</h2>
<div class="team3"><span class="tlabel">We are Team DiagNodes</span><span class="nm">Jhezra Tolentino</span><span class="nm">Paul Dacalan</span><span class="nm">Kishia Gaytano</span></div>
<div class="why3">A friend of ours got dengue.<br>We built EpiLag-PH so a health office sees the next outbreak coming.</div>
<div class="objrail obj3">
 <div class="ob"><span>01</span><b>Forecast</b><small>dengue cases 2 to 8 weeks ahead</small></div>
 <div class="ob"><span>02</span><b>Alert</b><small>flag the areas heading for an outbreak</small></div>
 <div class="ob"><span>03</span><b>Act</b><small>tell health offices what to do, and where to spend</small></div>
</div>
<blockquote class="onphoto">“Akala ko simpleng lagnat lang. Pagdating ng ikatlong araw, 40 °C na, ang sakit sa likod ng mata, tapos parang binabali yung mga kasu-kasuan ko.”
<small>“I thought it was just a fever. By day three it was 40 °C, my eyes hurt, and my joints felt like they were breaking.”</small><cite>A friend of ours</cite></blockquote>
<div class="foot"><span>Covers 86 provinces, 17 regions and Quezon City. Symptoms match those listed by WHO (2025).</span><span>4</span></div></section>""")

# ================================================================== 5 Literature: drivers + where studied
PX = 2.0
pins = [(120.98, 14.60, "Metro Manila", "Carvajal 2018, Sumi 2017"), (121.04, 14.68, "", ""),
        (125.61, 7.07, "Davao", "Iguchi 2018")]
pin_svg = ""
for lon, lat, lab, cit in pins:
    if not lab:
        continue
    x, y = lonlat_to_px(lon, lat, PX)
    pin_svg += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="11" fill="var(--red)" stroke="#fff" stroke-width="4"/>'
map5 = voxel_map(lambda u: "#CBD9CF", PX, pin_svg)
map5 = map5.replace(f'width="{192*PX}" height="{326*PX}"', 'width="300" height="509"')
lagrows = [("Humidity", 4, 4.4, "about 4 weeks", "Carvajal 2018, Xu 2020"),
           ("Rain", 5, 7, "5 to 7 weeks", "Sumi 2017, Carvajal 2018"),
           ("Temperature", 10, 18, "10 to 18 weeks", "Seposo 2023, Mordecai 2017")]
lw = 860
wx = lambda wk: 40 + wk / 20 * (lw - 80)  # noqa: E731
lr = "".join(f'<g transform="translate(0,{20+i*112})"><text x="0" y="0" class="mk big2">{n}</text><text x="0" y="30" class="mks">{t}, {c}</text><rect x="{wx(a):.0f}" y="46" width="{max(wx(b)-wx(a),16):.0f}" height="34" rx="8" fill="var(--accent)"/></g>' for i, (n, a, b, t, c) in enumerate(lagrows))
lr += "".join(f'<line x1="{wx(k):.0f}" x2="{wx(k):.0f}" y1="380" y2="392" class="axis"/><text x="{wx(k):.0f}" y="420" class="tick" text-anchor="middle">{k}</text>' for k in range(0, 21, 4))
lr += f'<line x1="{wx(0):.0f}" x2="{wx(20):.0f}" y1="380" y2="380" class="axis"/><text x="{wx(20):.0f}" y="452" class="tick" text-anchor="end">weeks before cases rise</text>'
heat = '''<svg viewBox="0 0 420 210" width="420" height="210"><path d="M10 190 C 120 180, 200 40, 262 40 S 380 160, 410 195" fill="none" stroke="var(--accent)" stroke-width="5"/>
<line x1="262" x2="262" y1="40" y2="195" stroke="var(--muted)" stroke-dasharray="4 5"/><text x="262" y="26" class="mk" text-anchor="middle">27.5 °C</text>
<text x="10" y="208" class="mks">cooler</text><text x="410" y="208" class="mks" text-anchor="end">hotter</text></svg>'''
S.append(slide(5, "Literature", "Related Literature", "What 19 studies say about weather and dengue, 9 of them in the Philippines.", f'''
<div class="lit"><div class="litmap">{map5}<div class="maplab">Single-site studies, pinned.<br>Nationwide: Seposo 2023, Buczak 2014, Xu 2020.</div></div>
<div class="litlags"><svg viewBox="0 0 {lw} 460" width="{lw}" height="460">{lr}</svg>
<div class="heatcard"><div class="kicker">Heat bends</div>{heat}<div class="cap">Risk rises with temperature, peaks near 27.5 °C, then falls (61 provinces, Seposo 2023).</div></div></div></div>
<div class="litnotes"><span><b>El Niño</b> shifts dengue over 2 to 5 years (van Panhuis 2015)</span><span><b>Elevation</b> tracks infection, not reported cases (Sy 2026)</span></div>''',
    "Full review: research/lit/rrl_matrix.csv and feature_evidence.csv. Lags as reported by each study."))

# ================================================================== 6 Gap matrix
rows6 = [("Olana et al. (2025)", "national, monthly", [0, 1, 0, 0]),
         ("Carvajal et al. (2018)", "Metro Manila, weekly", [0, 0, 0, 0]),
         ("Eligado et al. (2026)", "Quezon City, weekly", [0, 0, 0, 0]),
         ("Buczak et al. (2014)", "40 provinces, high or low", [1, 0, 1, 1]),
         ("EpiLag-PH", "104 areas, weekly counts", [1, 1, 1, 1])]
cols6 = ["Weekly, for many areas", "Gives a likely range", "Alerts scored for hits and false alarms", "Tested on several unseen years"]
cells = ""
for r, (n, d, vs) in enumerate(rows6):
    us = n == "EpiLag-PH"
    cells += f'<div class="gm-name{" us" if us else ""}"><b>{n}</b><small>{d}</small></div>'
    cells += "".join(f'<div class="gm-c{" on" if v else ""}{" us" if us else ""}">{"✓" if v else ""}</div>' for v in vs)
S.append(slide(6, "Literature", "Related Literature", "No Philippine study does all four. That is the gap EpiLag-PH fills.", f'''
<div class="gm"><div></div>{"".join(f'<div class="gm-h">{c}</div>' for c in cols6)}{cells}</div>
''',
    "Olana and Carvajal test one held-out year; Olana's ranges have no coverage check; Eligado compares alert thresholds without scoring hits; Buczak predicts classes, not counts. research/lit/positioning.md"))

# ================================================================== 7 Data
yr = lambda y: (y - 2010) / 16 * 820  # noqa: E731
src_rows = [("DOH via HDX", "86 provinces", [(2016, 2021.05)]), ("UPRI-NOAH", "17 regions", [(2016, 2020), (2022, 2026)]),
            ("UPRI-NOAH", "Quezon City", [(2010, 2026)]), ("ERA5 via Open-Meteo", "rain, heat, humidity", [(2015.5, 2026)])]
b7 = ""
for i, (n, d, spans) in enumerate(src_rows):
    y = 90 + i * 80
    b7 += f'<text x="0" y="{y+26}" class="mk">{n}</text><text x="0" y="{y+52}" class="mks">{d}</text>'
    for a, b_ in spans:
        b7 += f'<rect x="{250+yr(a):.0f}" y="{y+8}" width="{yr(b_)-yr(a):.0f}" height="38" rx="8" fill="var(--accent)" opacity=".85"/>'
gx, gw = 250 + yr(2020), yr(2022) - yr(2020)
b7 += f'<rect x="{gx:.0f}" y="178" width="{gw:.0f}" height="38" rx="8" fill="none" stroke="var(--red)" stroke-dasharray="6 5" stroke-width="2.5"/>'
tx = 250 + yr(2021.6)
b7 += f'<path d="M{tx-150:.0f} 34 C {tx-40:.0f} 34, {tx:.0f} 80, {tx:.0f} 170" fill="none" stroke="var(--red)" stroke-width="2.5"/><path d="M{tx-9:.0f} 158 L{tx:.0f} 172 L{tx+9:.0f} 158" fill="none" stroke="var(--red)" stroke-width="2.5"/>'
b7 += f'<text x="{tx-160:.0f}" y="42" class="hand" text-anchor="end" style="fill:var(--red)">no regional data, 2020 to 2021</text>'
b7 += "".join(f'<text x="{250+yr(y):.0f}" y="424" class="tick" text-anchor="middle">{y}</text>' for y in (2010, 2014, 2018, 2022, 2025))
raw = [["REGION", "YR", "WN", "DC_HDX", "RF_HDX"], ["REGION VII", "2019", "23", "153", "17.76"]]
clean = [["unit_id", "week", "cases", "rain_mm", "y_lag0"], ["R_REGION_VII", "2019-06-09", "153", "17.76", "5.04"]]
tbl = lambda rows, cls: f'<table class="dt {cls}">' + "".join("<tr>" + "".join(f"<{'th' if i==0 else 'td'}>{c}</{'th' if i==0 else 'td'}>" for c in r) + "</tr>" for i, r in enumerate(rows)) + "</table>"  # noqa: E731
steps7 = [("Match names to official codes", "location names to PSGC-based area codes, fixing typos such as “Basilig” for Bislig"),
          ("Fold cities into their area", "cities summed into their province or NCR district, giving 86 province units"),
          ("Merge split areas", "Maguindanao, split in 2022, kept as one unit with Cotabato City for 2016 to 2020"),
          ("Keep only complete weeks", "a week counts only if every reporting location sent data; otherwise it stays missing, never zero"),
          ("Epidemiological week to date", "“2019, week 23” becomes the week ending 9 Jun 2019"),
          ("Gap-free weekly calendar", "every area gets every week, so “4 weeks ago” always means 4 weeks"),
          ("Weather to weeks", "daily ERA5 at each area's centre: rain summed, temperature and humidity averaged"),
          ("Scale the counts", "log(cases + 1), so big provinces don't drown out small ones")]
st7 = "".join(f'<li><span>{k+1}</span><div><b>{a}</b><small>{b}</small></div></li>' for k, (a, b) in enumerate(steps7))
S.append(slide(7, "Data", "Data Sources and Cleaning", "Four public sources, cleaned in eight steps into one weekly table.", f"""
<div class="d7"><div class="d7l"><svg viewBox="0 0 1080 440" width="1000" height="407">{b7}</svg>
<div class="rawclean"><div><div class="kicker">Raw file</div>{tbl(raw, "raw")}</div><div class="arrowr">→</div><div><div class="kicker">Model table</div>{tbl(clean, "cl")}</div></div></div>
<ol class="steps7">{st7}</ol></div>""",
    "DOH via HDX; Pelitro (2026); ERA5 (Hersbach et al., 2020); PSA and OCHA. Example row: Region VII, week ending 9 Jun 2019 (research/results/extracts/weekly_series.csv.gz). Code: src/clean_dengue.py, src/fetch_weather.py, src/features.py."))

# ================================================================== 8 Features
groups8 = [("Recent cases", "8 inputs", "this week, 1 to 3 weeks back, 4 and 12 week averages, trend, same week last year", 0, 3, "var(--ink)"),
           ("Rain", "16 inputs", "each of the last 12 weeks, plus 4, 8 and 12 week totals, and heavy-rain days (50 mm or more) in 8 weeks", 0, 11, "var(--accent)"),
           ("Humidity", "5 inputs", "0, 2, 4, 6 and 8 weeks back", 0, 8, "var(--accent)"),
           ("Temperature", "6 inputs", "0, 2, 4, 6 and 8 weeks back, plus the 4 week maximum", 0, 8, "var(--accent)"),
           ("Time of year", "2 inputs", "sine and cosine, so December sits next to January", None, None, "var(--faint)"),
           ("Population", "1 input", "log of population", None, None, "var(--faint)")]
fw = 760
fx = lambda wk: 20 + wk / 12 * (fw - 40)  # noqa: E731
f8 = ""
for i, (n, cnt, d, a, b_, col) in enumerate(groups8):
    y = i * 92
    bar = f'<rect x="{fx(a):.0f}" y="20" width="{fx(b_)-fx(a)+14:.0f}" height="30" rx="7" fill="{col}"/>' if a is not None else '<text x="20" y="42" class="mks">no lag: known at forecast time</text>'
    f8 += f'<div class="fr"><div class="fn"><b>{n}</b><span>{cnt}</span><small>{d}</small></div><svg viewBox="0 0 {fw} 70" width="{fw}" height="70">{bar}</svg></div>'
axis8 = f'<svg viewBox="0 0 {fw} 50" width="{fw}" height="50"><line x1="20" x2="{fw-20}" y1="6" y2="6" class="axis"/>' + "".join(f'<text x="{fx(k):.0f}" y="38" class="tick" text-anchor="middle">{k}</text>' for k in (0, 2, 4, 6, 8, 10, 12)) + "</svg>"
S.append(slide(8, "Data", "Feature Engineering", "The literature's lags, turned into model inputs.", f'''
<div class="f8"><div class="frs">{f8}<div class="fr axisrow"><div class="fn"></div>{axis8}</div><div class="axlab">weeks before the forecast is made</div></div>
<div class="f8side"><div class="big">38</div><div class="cap">inputs per province forecast. Regions and Quezon City use 26: rain, but not heavy-rain days, temperature or humidity.</div>
<div class="rule2">Every input is known on the day the forecast is made. No future data, ever.</div></div></div>''',
    "src/features.py, feature_columns(). Temperature and humidity were tested for regions in the research (slide 15)."))

# ================================================================== 9 Model (technical)
S.append(slide(9, "Model", "Model", "Quantile LightGBM with conformal calibration: a forecast, a likely range, and an alert.", f'''
<div class="m9">
 <div class="m9a"><div class="kicker">Gradient-boosted trees, three per forecast distance</div>
  <div class="trees">{"".join(f'<div class="tq"><svg viewBox="0 0 120 110" width="120" height="110"><path d="M60 8 L60 40 M60 40 L28 70 M60 40 L92 70 M28 70 L14 100 M28 70 L42 100 M92 70 L78 100 M92 70 L106 100" stroke="var(--ink)" stroke-width="3" fill="none"/>{"".join(f"<rect x={cx-9} y={cy-9} width=18 height=18 rx=4 fill={col}/>" for cx, cy, col in [(60,8,"var(--accent)"),(28,70,"var(--ink)"),(92,70,"var(--ink)"),(14,100,"var(--accent)"),(42,100,"var(--accent)"),(78,100,"var(--accent)"),(106,100,"var(--accent)")])}</svg><b>{q}</b><small>{d}</small></div>' for q, d in [("10th", "low estimate"), ("50th", "middle"), ("90th", "high estimate")])}</div>
  <div class="cap">Each quantile is trained with <b class="ink">pinball (quantile) loss</b>, which penalises misses on one side more than the other. 3 quantiles × 4 distances = <b class="ink">12 models</b> per area set.</div></div>
 <div class="spec"><div class="kicker">Hyperparameters</div>
  <div class="sp"><span>n_estimators</span><b>{PARAMS["n_estimators"]}</b><small>trees added one by one</small></div>
  <div class="sp"><span>learning_rate</span><b>{PARAMS["learning_rate"]}</b><small>small steps, less overfitting</small></div>
  <div class="sp"><span>num_leaves</span><b>{PARAMS["num_leaves"]}</b><small>how detailed each tree can be</small></div>
  <div class="sp"><span>min_child_samples</span><b>{PARAMS["min_child_samples"]}</b><small>at least 30 weeks per leaf</small></div>
  <div class="sp"><span>subsample, colsample</span><b>{PARAMS["subsample"]}, {PARAMS["colsample_bytree"]}</b><small>80% of rows and inputs per tree</small></div></div>
 <div class="cqr"><div class="kicker">Conformalized quantile regression</div>
  <svg viewBox="0 0 470 240" width="470" height="240"><path d="M20 150 C 120 120, 220 140, 300 100 S 420 90, 450 80 L450 120 C 420 130, 340 140, 300 140 S 120 170, 20 175 Z" fill="var(--accent)" opacity=".18"/>
  <path d="M20 120 C 120 85, 220 105, 300 62 S 420 50, 450 40 L450 160 C 420 170, 340 182, 300 180 S 120 205, 20 210 Z" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-dasharray="7 6"/>
  {"".join(f'<circle cx="{x}" cy="{y}" r="6" fill="var(--ink)"/>' for x, y in [(60,160),(110,128),(160,190),(210,118),(260,96),(310,170),(360,74),(410,118),(440,60)])}
  </svg>
  <div class="cap">Hold out the last training year, measure how far real weeks fall outside the band, and widen it until <b class="ink">80%</b> fall inside.</div></div>
</div>''', "src/backtest.py (PARAMS, fit_quantiles, conformal_margin). Ke et al. (2017); Romano et al. (2019)."))

# ================================================================== 10 Validation (time split)
yrs = list(range(2016, 2026))
tests = [("Provinces", [2019, 2020], 2021), ("Regions and QC", [2019, 2023, 2024, 2025], 2026)]
g10 = ""
for name, tys, end in tests:
    for ty in tys:
        cells = ""
        for y in yrs:
            gap = name != "Provinces" and y in (2020, 2021)
            if y >= end or gap or y > ty:
                c = "none"
            elif y == ty:
                c = "test"
            elif y == max(v for v in yrs if v < ty and not (name != "Provinces" and v in (2020, 2021))):
                c = "cal"
            else:
                c = "train"
            cells += f'<i class="{c}"></i>'
        g10 += f'<div class="yrrow"><span>{name}, {ty}</span>{cells}</div>'
head10 = '<div class="yrrow head"><span></span>' + "".join(f"<i>{y}</i>" for y in yrs) + "</div>"
S.append(slide(10, "Model", "Validation", "Expanding-window time split: every test year is forecast blind.", f'''
<div class="v10"><div class="years">{head10}{g10}
<div class="legend2"><span><i class="train"></i>trained on</span><span><i class="cal"></i>calibration year</span><span><i class="test"></i>forecast blind</span></div>
</div>
<div class="v10side">
 <div class="vm"><b>24</b><span>checks: 6 test years × 4 forecast distances</span></div>
 <div class="vm"><b>No shuffling</b><span>rows are never mixed across time, unlike a random split</span></div>
 <div class="vm"><b>2 baselines</b><span>“same as this week” and “same week last year”</span></div>
 <div class="vm"><b>4 scores</b><span>error (MAE), range coverage, outbreaks caught, false alarms</span></div></div></div>''',
    "src/backtest.py, src/alerts.py; research/results/METHODS.md. An outbreak start is the first of 2 or more weeks above the epidemic line."))

# ================================================================== 11 Model comparison heat grid
mods = [("lightgbm", "LightGBM"), ("negbin", "Negative binomial"), ("random_forest", "Random forest"), ("sarimax", "SARIMAX"), ("blend_all4", "Average of the four")]
order = list(relp.index)


def heat(v):
    if v < 1:
        t = min((1 - v) / 0.4, 1)
        return f"rgba(18,128,74,{0.15 + 0.85*t:.2f})"
    t = min((v - 1) / 0.25, 1)
    return f"rgba(210,59,48,{0.2 + 0.8*t:.2f})"


hdr = ""
prev = None
for k, (p, ty, hh) in enumerate(order):
    lab = f'{"Prov" if p == "province" else "Reg"} {ty}'
    hdr += f'<div class="hg-h">{lab if (p, ty) != prev else ""}</div>'
    prev = (p, ty)
rowsg = ""
for mkey, mlab in mods:
    rowsg += f'<div class="hg-n{" us" if mkey == "lightgbm" else ""}">{mlab}<small>{(str(wins[mkey]) + " checks with the lowest error") if mkey in four else "not a separate model"}</small></div>'
    for k, idx in enumerate(order):
        v = relp.loc[idx, mkey]
        gap = " gap" if k % 4 == 0 and k else ""
        rowsg += f'<div class="hg-c{gap}" style="background:{heat(v)}" title="{v:.2f}"></div>'
hz = "".join(f'<div class="hg-hz">{hh}</div>' for (_, _, hh) in order)
S.append(slide(11, "Model", "Model Comparison", "Four methods on the same test, plus their average. Each square is one check.", f'''
<div class="hg"><div></div>{hdr}<div class="hg-n sm">weeks ahead</div>{hz}{rowsg}</div>
<div class="hgleg"><span>beat “same as this week” by more</span><i style="background:rgba(18,128,74,1)"></i><i style="background:rgba(18,128,74,.5)"></i><i style="background:rgba(18,128,74,.15)"></i><i style="background:rgba(210,59,48,.3)"></i><i style="background:rgba(210,59,48,1)"></i><span>did worse than “same as this week”</span></div>
<div class="hgfacts"><span><b>{wins['lightgbm']} of 24</b> lowest error: LightGBM</span><span><b>{wins['negbin']}</b> negative binomial</span><span><b>{wins['sarimax']}</b> SARIMAX</span><span><b>{wins['random_forest']}</b> random forest</span></div>''',
    "Color = error divided by the error of “same as this week” (research/results/model_comparison.csv, rel_mae_vs_persistence). Prov = provinces; Reg = regions and Quezon City."))

# ================================================================== 12 Decisions and trade-offs
W2, H2, L2, R2, T2, B2 = 760, 420, 80, 240, 24, 56
X2 = lambda hh: L2 + (hh - 2) / 6 * (W2 - L2 - R2)  # noqa: E731
Y2 = lambda v: T2 + (1 - (v + 2) / 16) * (H2 - T2 - B2)  # noqa: E731
g2 = "".join(f'<line x1="{L2}" x2="{W2-R2}" y1="{Y2(v):.1f}" y2="{Y2(v):.1f}" class="grid"/><text x="{L2-12}" y="{Y2(v)+6:.1f}" class="tick" text-anchor="end">{"+" if v>0 else ""}{v}%</text>' for v in (0, 4, 8, 12))
x2t = "".join(f'<text x="{X2(hh):.1f}" y="{H2-B2+34}" class="tick" text-anchor="middle">{hh} wk</text>' for hh in (2, 4, 6, 8))
l2 = f'<line x1="{L2}" x2="{W2-R2}" y1="{Y2(0):.1f}" y2="{Y2(0):.1f}" stroke="var(--accent)" stroke-width="4"/><text x="{L2+8}" y="{Y2(0)+32:.1f}" class="mk" style="fill:var(--accent)">LightGBM = 0</text>'
for col, nm, color, wdt in [("negbin", "Neg. binomial", "var(--ink)", 3), ("random_forest", "Random forest", "var(--faint)", 2), ("sarimax", "SARIMAX", "var(--faint)", 2)]:
    pts = [(X2(hh), Y2(rel.loc[hh, col])) for hh in (2, 4, 6, 8)]
    l2 += f'<path d="{path(*zip(*pts))}" fill="none" stroke="{color}" stroke-width="{wdt}"/><circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="5" fill="{color}"/>'
    l2 += f'<text x="{pts[-1][0]+14:.1f}" y="{pts[-1][1]+6:.1f}" class="{"mk" if wdt==3 else "lbl"}">{nm} {rel.loc[8, col]:+.0f}%</text>'
lims = [("Record surges", "2019 rose past anything in training. Trees can't extrapolate; a simpler model did better at 2 weeks."),
        ("Quiet years", "2023 was the flattest year, and its calibration year's model ran low, so the range came out too wide (92%)."),
        ("False alarms, on purpose", "About half of Watch alerts are false. A Watch costs a clean-up drive; Outbreak warning is stricter."),
        ("Better inputs, not yet live", "Neighbours' cases, temperature and humidity improved 21 of 24 checks, but were chosen after seeing the test years.")]
S.append(slide(12, "Model", "Decisions and Trade-offs", "Why we kept LightGBM, and where it still falls short.", f'''
<div class="d14"><div><div class="kicker">How much less accurate than LightGBM, by weeks ahead</div><svg viewBox="0 0 {W2} {H2}" width="{W2}" height="{H2}">{g2}{x2t}{l2}</svg>
<div class="why"><span><b>{wins['lightgbm']} of 24</b> most accurate</span><span><b>holds up</b> at 8 weeks</span><span><b>explains</b> each forecast</span></div>
<div class="cap">The average of the four was slightly more accurate, but caught fewer outbreaks early ({warn['blend_all4']}% vs {warn['lightgbm']}%). For early warning, a missed outbreak costs more.</div></div>
<div class="limcol"><div class="kicker">Where it falls short</div>{"".join(f'<div class="lim2"><b>{a}</b><p>{b}</p></div>' for a, b in lims)}</div></div>''',
    "research/results/model_comparison.csv; research/analysis/causes.md; research/results/README.md (final variables)."))

# ================================================================== 13 Results: QC
W, H, L, R, T, B = 1180, 600, 70, 30, 30, 60
x0, x1 = qcb.target_week.min(), qcb.target_week.max()
X = lambda d: L + (pd.Timestamp(d) - x0) / (x1 - x0) * (W - L - R)  # noqa: E731
Y = lambda v: T + (1 - v / 700) * (H - T - B)  # noqa: E731
band = path([X(d) for d in qcb.target_week], [Y(v) for v in qcb.q90]) + " L" + " L".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in zip(qcb.target_week[::-1], qcb.q10[::-1])) + " Z"
act = path([X(d) for d in qcb.target_week], [Y(v) for v in qcb.actual])
ln = path([X(d) for d in qcb.target_week], [Y(v) for v in qcb.epidemic])
dots = "".join(f'<circle cx="{X(r.target_week):.1f}" cy="{Y(r.actual):.1f}" r="6" fill="var(--red)" stroke="var(--bg)" stroke-width="2"/>' for r in qcb.itertuples() if r.actual > r.epidemic)
grid = "".join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/><text x="{L-12}" y="{Y(v)+6:.1f}" class="tick" text-anchor="end">{v}</text>' for v in range(0, 701, 200))
xt = "".join(f'<text x="{X(m):.1f}" y="{H-B+34}" class="tick" text-anchor="middle">{m.strftime("%b")}</text>' for m in pd.date_range("2024-09-01", "2025-03-01", freq="MS"))


def marker(date, label, sub, dy, color="var(--ink)", left=False):
    x = X(date)
    tx, anc = (x - 10, "end") if left else (x + 10, "start")
    return (f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{H-B}" stroke="{color}" stroke-width="2" opacity=".55"/>'
            f'<text x="{tx:.1f}" y="{T+dy}" class="mk" text-anchor="{anc}">{label}</text><text x="{tx:.1f}" y="{T+dy+26}" class="mks" text-anchor="{anc}">{sub}</text>')


pk = qcb.loc[qcb.actual.idxmax()]
svg11 = f'''<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}">{grid}{xt}<path d="{band}" fill="var(--accent)" opacity=".16"/>
<path d="{ln}" fill="none" stroke="var(--red)" stroke-width="2" stroke-dasharray="8 6"/><path d="{act}" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linejoin="round"/>{dots}
{marker("2024-09-15", "Watch issued", "15 Sep", 20, "var(--amber)")}{marker("2024-10-20", "Crossed the line", "20 Oct", 20)}
<line x1="{X("2024-09-15"):.1f}" x2="{X("2024-10-20"):.1f}" y1="{T+96}" y2="{T+96}" stroke="var(--ink)" stroke-width="2"/>
<text x="{(X("2024-09-15")+X("2024-10-20"))/2:.1f}" y="{T+128}" class="mk" text-anchor="middle">5 weeks</text>
{marker("2025-02-15", "Outbreak declared", "15 Feb", 20, left=True)}
<text x="{X(pk.target_week)+16:.1f}" y="{Y(pk.actual)+8:.1f}" class="mk">{int(pk.actual)}</text><text x="{X(pk.target_week)+16:.1f}" y="{Y(pk.actual)+34:.1f}" class="mks">peak week</text>
<text x="{W-R}" y="{Y(qcb.epidemic.iloc[-1])+34:.1f}" class="lbl" text-anchor="end">epidemic line</text></svg>'''
S.append(slide(13, "Results", "Results", "It saw Quezon City's outbreak coming five weeks early.", f'''
<div class="row"><div><div class="legend"><span><i style="background:var(--accent);opacity:.35"></i>likely range, forecast 4 weeks ahead</span><span><i style="background:var(--ink)"></i>reported cases</span><span><i style="background:var(--red);width:14px;height:14px;border-radius:50%"></i>week above the epidemic line</span></div>{svg11}
</div>
<div class="stack"><div class="card"><div class="big green">5 weeks</div><div class="cap">of warning before Quezon City crossed its epidemic line in 2024</div></div>
<div class="card"><div class="big">{int(pk.q50)}</div><div class="cap">forecast for the peak week, against {int(pk.actual)} reported. The alert was right; the size was not.</div></div></div></div>''',
    "Quezon City, weekly reported cases, Sep 2024 to Mar 2025. Forecasts use only data available at the time. Sources: Pelitro (2026); EpiLag-PH backtests."))

# ================================================================== 14 Results: nationwide
COL = {"hit": "#D23B30", "miss": "#14211B", "no": "#D8E0DA"}


def cat(u):
    v = rep_units.get(u)
    if not v:
        return COL["no"]
    if v[5] == "warning":
        return COL["hit"] if v[0] in ("watch", "warning") else COL["miss"]
    return COL["no"]


map12 = voxel_map(cat, 2.0)
sk = []
for p, lab in (("province", "Provinces"), ("region_qc", "Regions and QC")):
    d = bp[p][bp[p].horizon == 4]
    for r in d.itertuples():
        sk.append((f"{lab}, {r.test_year}", r.skill_vs_seasonal * 100, r.skill_vs_persistence * 100))
bw12 = 520
bars12 = ""
for i, (lab, s1, s2) in enumerate(sk):
    y = i * 74
    bars12 += f'<text x="0" y="{y+28}" class="mk">{lab}</text>'
    bars12 += f'<rect x="250" y="{y+8}" width="{max(s1,0)/100*bw12:.0f}" height="24" rx="5" fill="var(--accent)"/><text x="{250+max(s1,0)/100*bw12+10:.0f}" y="{y+28}" class="mks">{s1:.0f}%</text>'
    w2 = abs(s2) / 100 * bw12
    bars12 += f'<rect x="250" y="{y+38}" width="{max(w2,3):.0f}" height="20" rx="5" fill="{"var(--ink)" if s2 >= 0 else "var(--red)"}"/><text x="{250+max(w2,3)+10:.0f}" y="{y+55}" class="mks">{"" if s2 >= 0 else "+"}{abs(s2):.0f}% {"less" if s2 >= 0 else "more"}</text>'
S.append(slide(14, "Results", "Results", f"Nationwide, the 2019 replay flagged {claim['flagged']} of {claim['crossed']} provinces before they crossed the line.", f'''
<div class="r12"><div class="mapwrap">{map12}
<div class="mlegend"><span><i style="background:{COL['hit']}"></i>crossed the line, flagged 4 weeks ahead <b>{claim['flagged']}</b></span><span><i style="background:{COL['miss']}"></i>crossed, missed <b>{claim['crossed']-claim['flagged']}</b></span><span><i style="background:{COL['no']}"></i>did not cross</span></div></div>
<div><div class="kicker">Error cut, 4 weeks ahead</div><div class="lg12"><span><i style="background:var(--accent)"></i>vs “same week last year”</span><span><i style="background:var(--ink)"></i>vs “same as this week”</span></div>
<svg viewBox="0 0 900 450" width="900" height="450">{bars12}</svg>
<div class="cap">Ranges held 70 to 92% of real weeks across test years (target 80%).</div></div></div>''',
    "Forecasts made 2 Jun 2019 for 30 Jun 2019 (docs/data/replay_2019-06-02.json). Error: reports/backtest_province.csv, reports/backtest_region_qc.csv (mean absolute error)."))

# ================================================================== 15 Key drivers: SHAP + factor tests
# a) SHAP waterfall for QC's latest 4-week forecast
wf_order = ["Recent cases", "Time of year", "Rain", "Population"]
wfv = [float(qc_drv.get(k, 0)) for k in wf_order]
mx = max(abs(v) for v in wfv)
wf = ""
AX, SC = 430, 190
for i, (k, v) in enumerate(zip(wf_order, wfv)):
    w = abs(v) / mx * SC
    x = AX if v >= 0 else AX - w
    y = i * 58
    wf += f'<text x="0" y="{y+31}" class="mk">{k}</text><rect x="{x:.0f}" y="{y+10}" width="{max(w,3):.0f}" height="30" rx="6" fill="{"var(--red)" if v > 0 else "var(--accent)"}"/>'
wf = f'<svg viewBox="0 0 640 240" width="640" height="240"><line x1="{AX}" x2="{AX}" y1="0" y2="232" class="axis"/>{wf}</svg>'
# b) share by horizon (stacked columns)
sh = shap_cur.pivot_table(index="horizon", columns="group", values="share").fillna(0)
cols_sh = [("cases", "Recent cases", "var(--ink)"), ("season", "Time of year", "var(--faint)"), ("rain", "Rain", "var(--accent)"), ("population", "Population", "var(--dim2)")]
st = ""
for i, hh in enumerate(sh.index):
    y0 = 300
    for g, _, colr in cols_sh:
        v = sh.loc[hh, g] if g in sh.columns else 0
        hgt = v * 280
        y0 -= hgt
        st += f'<rect x="{40+i*110}" y="{y0:.1f}" width="70" height="{hgt-2:.1f}" rx="3" fill="{colr}"/>'
    st += f'<text x="{75+i*110}" y="326" class="tick" text-anchor="middle">{hh} wk</text>'
    st += f'<text x="{75+i*110}" y="{300-sh.loc[hh, ["cases","season"]].sum()*280 - sh.loc[hh,"rain"]*140 + 6:.0f}" class="lbl" text-anchor="middle" style="fill:#fff">{sh.loc[hh,"rain"]*100:.0f}%</text>'
st = f'<svg viewBox="0 0 480 340" width="480" height="340">{st}</svg>'
# c) factor tests dot plot
fac = []
for grp, lab in [("heat", "Temperature"), ("humidity", "Humidity"), ("rain", "Rain"), ("enso", "El Niño"), ("topography", "Elevation"), ("population", "Population")]:
    for p in ("region_qc", "province"):
        d = fg[(fg["mode"] == "add") & (fg.group == grp) & (fg.panel == p)]
        if len(d):
            fac.append((lab, p, d.change_pct.median(), int((d.change_pct < 0).sum()), len(d)))
for p in ("region_qc", "province"):
    d = pf[(pf.group == "neighbours") & (pf["mode"] == "add_to_plus") & (pf.panel == p)] if "neighbours" in set(pf.group) else pf.iloc[0:0]
    if len(d):
        fac.append(("Neighbours' cases", p, d.change_pct.median(), int((d.change_pct < 0).sum()), len(d)))
labs_f = list(dict.fromkeys(f[0] for f in fac))
dx = lambda v: 290 + v / 8 * 220  # noqa: E731
dp = f'<line x1="{dx(0)}" x2="{dx(0)}" y1="0" y2="{len(labs_f)*54}" class="axis"/>'
dp += f'<text x="{dx(-8)}" y="{len(labs_f)*54+30}" class="tick">helped</text><text x="{dx(8)}" y="{len(labs_f)*54+30}" class="tick" text-anchor="end">hurt</text>'
for i, lab in enumerate(labs_f):
    y = i * 54 + 26
    dp += f'<text x="0" y="{y+7}" class="mks">{lab}</text>'
    for _, p, v, nh, nn in [f for f in fac if f[0] == lab]:
        vv = max(min(v, 8), -8)
        shape = f'<circle cx="{dx(vv):.0f}" cy="{y}" r="10" fill="{"var(--accent)" if v < 0 else "var(--red)"}"/>' if p == "region_qc" else f'<rect x="{dx(vv)-9:.0f}" y="{y-9}" width="18" height="18" rx="3" fill="{"var(--accent)" if v < 0 else "var(--red)"}"/>'
        dp += shape
dp = f'<svg viewBox="0 0 520 {len(labs_f)*54+40}" width="520" height="{len(labs_f)*54+40}">{dp}</svg>'
S.append(slide(15, "Results", "Key Drivers", "What the forecast relies on, and which factors earn their place.", f"""
<div class="k15">
 <div class="kp"><div class="kicker">1  SHAP: one forecast, explained</div><div class="take">Recent cases pulled Quezon City's forecast down; the season pushed it up.</div>{wf}
  <div class="legend3"><span><i style="background:var(--red)"></i>raised the forecast</span><span><i style="background:var(--accent)"></i>lowered it</span></div></div>
 <div class="kp"><div class="kicker">2  Further ahead, weather matters more</div><div class="take">Rain's share of attention: <b class="green">11%</b> at 2 weeks, <b class="green">24%</b> at 8.</div>{st}
  <div class="legend3"><span><i style="background:var(--ink)"></i>recent cases</span><span><i style="background:var(--faint)"></i>season</span><span><i style="background:var(--accent)"></i>rain</span></div></div>
 <div class="kp"><div class="kicker">3  Each factor, tested</div><div class="take">Added to recent cases and season: did the error drop?</div>{dp}
  <div class="legend3"><span>● regions and QC</span><span>■ provinces</span></div></div>
</div>""", "SHAP: Lundberg and Lee (2017). Quezon City latest forecast (region_qc_drivers.json); shares: shap_groups.csv; tests: feature_groups.csv (add), proposed_features.csv (neighbours)."))

# ================================================================== 16 System: health offices
badges = [(1, 17.6, 32), (2, 48.4, 29), (3, 20.6, 49.4), (4, 20.6, 73)]
bd = "".join(f'<span class="badge-n" style="left:{x}%;top:{y}%">{n}</span>' for n, x, y in badges)
expl = [("Alert level", "Watch: the high estimate crosses the city's own epidemic line"),
        ("Likely range", "251 cases expected in 4 weeks, likely between 152 and 360"),
        ("What to do", "a checklist for this week, weeks 1 to 3, and every week"),
        ("Against the line", "forecast band, reported cases and the epidemic line on one chart")]
ex = "".join(f'<div class="ex16"><span>{k+1}</span><div><b>{a}</b><small>{b}</small></div></div>' for k, (a, b) in enumerate(expl))
thumbs = [("app_onboarding.png", "Onboarding guide"), ("app_map.png", "Outbreak map"), ("app_budget.png", "Budget plan")]
th = "".join(f'<figure class="thumb"><img src="assets/{f}"><figcaption>{c}</figcaption></figure>' for f, c in thumbs)
S.append(slide(16, "System", "The System, for Health Offices", "From a forecast to this week's action plan, for Quezon City on 15 Sep 2024.", f'''
<div class="sys"><div class="lapwrap">{laptop("assets/app_unit.png", 960).replace('<div class="cam"></div>', '<div class="cam"></div>' + f'<div class="bdl">{bd}</div>')}</div>
<div class="sysside">{ex}<div class="thumbs">{th}</div><div class="try2"><img src="{QR_URI}" alt="QR code to epilag.vercel.app"><div><span>Try it live</span><b>epilag.vercel.app</b></div></div></div></div>''',
    "Live app (epilag.vercel.app), area detail page, replay of the forecast made 15 Sep 2024."))

# ================================================================== 17 Residents and Dengue Drill
S.append(slide(17, "System", "The System, for Residents and Training", "Plain words for households. A game that lets you feel the five weeks.", f'''
<div class="s17"><div class="phonewrap">{phone("assets/phone_public_fil.png", 600)}<div class="cap" style="width:290px;font-size:20px">Residents' page in Filipino</div></div>
<div class="drill"><div class="dpair"><figure><img src="assets/drill_title.png"><figcaption><b>Dengue Drill:</b> pick a real outbreak to run</figcaption></figure>
<figure><img src="assets/drill_r2_board.png"><figcaption><b>In play:</b> the outbreak board, with EpiLag-PH intel</figcaption></figure></div>

<div class="kicker" style="margin-top:26px">When the computer player followed EpiLag-PH, 2019 missions</div>
<div class="ttb"><div class="b g" style="flex:11"><b>11</b> regions, more cases averted</div><div class="b n" style="flex:1"><b>1</b></div><div class="b r" style="flex:5"><b>5</b> fewer</div></div></div></div>''',
    "Live app and Dengue Drill (epilag.vercel.app). Drill result checked in tests/test_drill_rules.py."))

# ================================================================== 18 Scaling roadmap
# First barangay = highest average yearly cases of QC's 142 (UPRI NOAH 2010-2025): Batasan Hills, 327 a year.
# Cases averted per season = season cases x 65% in the 24 busiest weeks (QC median, 2014-24 seasons)
#   x 30% of residents covered per 8-week round (src/allocate.py max coverage) x effect 10/30/50% (allocate.py).
qcb = pd.read_csv(ROOT / "data/raw/upri_noah/QC_YearlyData-Barangay(CSV).csv")
yrs = [f"DC_{y}" for y in range(2010, 2026)]
qcb["avg"] = qcb[yrs].mean(axis=1)
first = qcb.sort_values("avg", ascending=False).iloc[0]
assert first.Barangay == "Batasan Hills"
D2 = ["Batasan Hills", "Payatas", "Commonwealth", "Holy Spirit", "Bagong Silangan"]
r4 = ["DC_2022", "DC_2023", "DC_2024", "DC_2025"]
typ_b, typ_d2, typ_qc = first[r4].mean(), qcb[qcb.Barangay.isin(D2)][r4].sum().mean(), qcb[r4].sum().mean()
d2_share = qcb[qcb.Barangay.isin(D2)][r4].sum().sum() / qcb[r4].sum().sum()
F = [0.65 * 0.30 * e for e in (0.10, 0.30, 0.50)]
av = lambda cases: [round(cases * f) for f in F]  # noqa: E731
avB, avB25, avD2, avQC = av(typ_b), av(first.DC_2025), av(typ_d2), av(typ_qc)
avDec = [round(v * 0.65) for v in avB]  # Jul-Dec holds ~65% of a QC season
POP_B, POP_QC, PESO = 168_770, 3_084_270, 15  # PSA 2024 census (POPCEN); app's example cost per resident covered
round_b, round_qc = POP_B * 0.30 * PESO / 1e6, POP_QC * 0.30 * PESO / 1e6
print("slide 18:", first.Barangay, round(first.avg), "typical", typ_b, avB, avB25, avDec, "D2", round(typ_d2), avD2, round(d2_share, 3), "QC", round(typ_qc), avQC, round(round_b, 2), round(round_qc, 1))

months = [("Setup", 2, "data link"), ("Shadow run", 4, "forecasts scored, no action"), ("Live: rainy season", 6, "a Watch triggers clean-up within a week"),
          ("Early-year tail", 3, "2025 peaked in Feb"), ("Evaluate", 3, "go or no-go")]
seg = "".join(f'<div class="mseg m{i}" style="flex:{n}"><b>{name}</b><small>{what}</small></div>' for i, (name, n, what) in enumerate(months))
ticks = "".join(f'<span style="left:{i / 18 * 100:.3f}%">{m}</span>' for i, m in [(0, "Jan 2027"), (6, "Jul"), (12, "Jan 2028"), (18, "Jun 2028")])
res = [("Jun 2027", "Forecasts scored live", "first clean-up round before the rains"),
       ("Dec 2027", f"{avDec[1]} fewer cases", f"range {avDec[0]} to {avDec[2]}"),
       ("Jun 2028", "Lead time, response and false alarms scored", f"{avB[1]} fewer cases expected ({avB[0]} to {avB[2]}); {avB25[1]} in a 2025-sized season")]
resh = "".join(f'<div class="res"><em>{d}</em><b>{t}</b><small>{s}</small></div>' for d, t, s in res)
steps = [("2", "District 2", "Jul 2028", f"+ Payatas, Commonwealth, Holy Spirit, Bagong Silangan: {d2_share*100:.0f}% of the city's cases",
          avD2, "₱0.45M a round per 100,000 residents"),
         ("3", "All of Quezon City", "Jul 2029", "142 barangays, " + f"{POP_QC/1e6:.2f}" + " million people; money goes first where it averts the most cases per peso",
          avQC, f"₱{round_qc:.0f}M per citywide round"),
         ("4", "NCR, then national", "from 2030", "regional epidemiology units, then the DOH Epidemiology Bureau; province forecasts already run weekly",
          None, "one scheduled job, open data")]
sth = "".join(f'<div class="sstep"><div class="shead"><span>{n}</span><div class="sn"><b>{t}</b><em>{w}</em></div>'
              + (f'<div class="sv"><b>{v[1]}</b><small>fewer cases a season<br>range {v[0]} to {v[2]}</small></div>' if v else "")
              + f'</div><p>{d}</p><p class="c">{c}</p></div>' for n, t, w, d, v, c in steps)
body18 = f"""
<div class="s18"><div class="pilot"><div class="ptag"><span>1</span><div><b>Batasan Hills, Quezon City</b><small>the most dengue cases of the city's 142 barangays: {first.avg:.0f} a year since 2010, {int(first.DC_2025)} in 2025; about {POP_B/1000:.0f},000 people</small></div></div>
<div class="mbar">{seg}</div><div class="mticks">{ticks}</div>
<div class="kicker">Expected results (estimates), compared with Payatas, Commonwealth and Holy Spirit</div>
<div class="results">{resh}</div>
<p class="pass"><b>Pass mark:</b> a Watch 4+ weeks before cases cross the epidemic line, clean-up within a week, few false alarms.</p>
<div class="bcost"><div><b>₱0</b><small>to run EpiLag-PH; about 4 staff hours a week</small></div><div><b>₱{round_b:.2f}M</b><small>per clean-up round; 3 rounds: ₱{3*round_b:.1f}M a season, less if it shifts clean-ups already planned</small></div></div></div>
<div class="scale"><div class="kicker">Then grow, one step at a time</div>{sth}</div></div>"""
S.append(slide(18, "Impact", "Impact and Scaling Plan", "Start in Batasan Hills, Quezon City's barangay with the most dengue cases. Prove it. Then grow.", body18,
    "Estimates. Cases averted = season cases × 65% in the 24 busiest weeks × 30% of residents reached × effect 10/30/50% (Bowman 2016). Clean-up round: 30% of residents at the app's example cost of ₱15 each. Population: PSA 2024 census. No partnership is claimed."))

# ================================================================== 19 Outro
S.append(f'''<section class="slide dark outro"><img class="half" src="assets/frog_outro.png" alt="The EpiLag-PH frog catching a mosquito">{top(None)}
<div class="outrotext"><div class="alertcard"><span>EpiLag-PH, Quezon City</span><b>Watch</b><small>5 weeks ahead</small></div>
<h1 class="statement">Next rainy season, we don't have to wait for the count.</h1>
<p class="close">Dengue is common.<br>Common shouldn't mean <span class="red">acceptable</span>.</p><div class="tryd"><img src="{QR_URI}" alt=""><b>epilag.vercel.app</b></div></div>
<div class="foot"><span>Team DiagNodes, PJDSC 2026</span><span>19</span></div></section>''')

# ================================================================== 20 References
refs = (BUILD / "references.html").read_text(encoding="utf8")
S.append(slide(20, None, "References", "APA 7th edition.", f'<div class="refs">{refs}</div>', ""))

CSS = (BUILD / "deck.css").read_text(encoding="utf8") + (BUILD / "deck_v2.css").read_text(encoding="utf8") + (BUILD / "deck_v4.css").read_text(encoding="utf8")
FONTS = "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500;1,700&family=Caveat:wght@600;700&family=IBM+Plex+Mono:wght@500;600&display=swap"
html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>EpiLag-PH, PJDSC 2026 final</title>
<link href="{FONTS}" rel="stylesheet"><style>{CSS}</style></head><body>{"".join(S)}</body></html>'''
(OUT / "index.html").write_text(html, encoding="utf8")
print("slides:", len(S), "| weeks above:", weeks_above, "| wins:", wins.to_dict(), "| claim:", claim, "| qc drivers:", qc_drv.round(3).to_dict())
