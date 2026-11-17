"""Build research/EpiLag-PH-research-paper.pdf from research/writeup/paper.md.

Steps:
1. Draw the four figures from the result files into research/writeup/figures/ (SVG, so GitHub shows them too).
2. Convert paper.md to HTML (Python-Markdown with tables), keeping the $...$ and $$...$$ math untouched.
3. Print it to A4 PDF with Playwright's Chromium. KaTeX 0.16.22 is loaded from jsDelivr to typeset the math,
   so the build needs a network connection.

Needs: pandas, matplotlib, markdown, playwright (`playwright install chromium`).
Usage: python research/writeup/build_paper.py
"""
import base64
import html as htmllib
import json
import re
import sys
from pathlib import Path

import markdown
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = HERE / "figures"
RESULTS = ROOT / "research" / "results"
WEB = ROOT / "site" / "public" / "web" / "data"
OUT = ROOT / "research" / "EpiLag-PH-research-paper.pdf"
sys.path.insert(0, str(ROOT / "src"))
from thresholds import thresholds  # noqa: E402

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE, ORANGE, GREEN, AMBER, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e8a33d", "#c8372d"
TEST_SHADE = "#efeee8"
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.22/dist"

plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.titlesize": 9.5, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "legend.frameon": False,
})


def save(fig, name: str) -> None:
    fig.savefig(FIG / name, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def weekly_total(ws: pd.DataFrame) -> pd.Series:
    s = ws.groupby("week").cases.sum(min_count=1)
    return s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="7D"))  # NaN over data gaps


def fig1_weekly_cases() -> None:
    ws = pd.read_csv(RESULTS / "extracts" / "weekly_series.csv.gz", parse_dates=["week"])
    prov = weekly_total(ws[ws.panel == "province"])
    reg = weekly_total(ws[(ws.panel == "region_qc") & (ws.unit_id != "QC")])
    qc = weekly_total(ws[ws.unit_id == "QC"])
    panels = [("(a) 86 provinces", prov, [2019, 2020]), ("(b) 17 regions", reg, [2019, 2023, 2024, 2025]),
              ("(c) Quezon City", qc, [2019, 2023, 2024, 2025])]
    fig, axes = plt.subplots(3, 1, figsize=(6.6, 6.4))
    for ax, (title, s, years) in zip(axes, panels):
        for y in years:
            ax.axvspan(pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31"), color=TEST_SHADE, lw=0)
            ax.text(pd.Timestamp(f"{y}-07-01"), 1.0, str(y), transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=7, color=MUTED)
        ax.plot(s.index, s.values, color=INK, lw=1.0)
        ax.set_title(title, pad=14)
        ax.set_ylabel("Cases per week")
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2 if s.index.min().year < 2015 else 1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(axis="x", visible=False)
    fig.tight_layout(h_pad=1.2)
    save(fig, "fig1_weekly_cases.svg")


def web_table(name: str, units: list[str]) -> pd.DataFrame:
    d = pd.DataFrame(json.loads((WEB / name).read_text(encoding="utf-8"))["cols"])
    d["unit_id"] = d.u.map(lambda i: units[i])
    return d


def fig2_qc() -> None:
    units = json.loads((WEB / "meta.json").read_text(encoding="utf-8"))["panels"]["region_qc"]["units"]
    hist = web_table("region_qc_history.json", units)
    hist["week"] = pd.to_datetime(hist.week, unit="D")
    bt = web_table("region_qc_backtest.json", units)
    bt["target_week"] = pd.to_datetime(bt.target_week, unit="D")
    qc = bt[(bt.unit_id == "QC") & (bt.horizon == 4) & bt.test_year.isin([2024, 2025])]
    parts = []
    for y, g in qc.groupby("test_year"):  # the epidemic line for year Y uses only years before Y
        thr = thresholds(hist[hist.week < f"{y}-01-01"][["unit_id", "week", "cases"]])
        g = g.assign(woy=g.target_week.dt.isocalendar().week.astype(int).clip(upper=52))
        parts.append(g.merge(thr[thr.unit_id == "QC"][["woy", "epidemic"]], on="woy"))
    q = pd.concat(parts).sort_values("target_week")
    q = q[(q.target_week >= "2024-09-01") & (q.target_week <= "2025-04-30")]
    level = (q.q90 > q.epidemic).astype(int) + (q.q50 > q.epidemic).astype(int)

    fig, (ax, strip) = plt.subplots(2, 1, figsize=(6.6, 3.9), sharex=True, gridspec_kw={"height_ratios": [9, 1]})
    ax.fill_between(q.target_week, q.q10, q.q90, color=BLUE, alpha=0.16, lw=0, label="Forecast 10–90% range")
    ax.plot(q.target_week, q.q50, color=BLUE, lw=1.4, label="Forecast median (4 weeks ahead)")
    ax.plot(q.target_week, q.epidemic, color=INK2, lw=1.0, ls=(0, (4, 3)), label="Epidemic line")
    ax.plot(q.target_week, q.actual, color=INK, lw=1.6, marker="o", ms=2.2, label="Reported cases")
    peak = q.loc[q.actual.idxmax()]
    ax.annotate(f"Peak: {peak.actual:.0f} cases\n(forecast {peak.q50:.0f})", (peak.target_week, peak.actual),
                xytext=(-92, -6), textcoords="offset points", fontsize=7.5, color=INK2,
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.7})
    declared = pd.Timestamp("2025-02-15")
    ax.axvline(declared, color=RED, lw=0.8, ls=":")
    ax.text(declared, 0.97, "City declares\noutbreak, 15 Feb", transform=ax.get_xaxis_transform(), ha="right",
            va="top", fontsize=7.5, color=RED)
    ax.set_ylabel("Cases per week")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", fontsize=7.5)
    ax.grid(axis="x", visible=False)
    colors = {0: "#f2f1ec", 1: AMBER, 2: RED}
    strip.bar(q.target_week, 1, width=6.5, color=[colors[v] for v in level], align="center")
    strip.set_yticks([])
    strip.set_ylim(0, 1)
    strip.grid(False)
    strip.spines[["left", "bottom"]].set_visible(False)
    strip.text(0, 1.15, "Alert level of the 4-week forecast:  ", transform=strip.transAxes, fontsize=7.5, color=INK2)
    strip.text(0.37, 1.15, "■ Watch", transform=strip.transAxes, fontsize=7.5, color=AMBER)
    strip.text(0.47, 1.15, "■ Outbreak warning", transform=strip.transAxes, fontsize=7.5, color=RED)
    strip.xaxis.set_major_locator(mdates.MonthLocator())
    strip.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.tight_layout(h_pad=1.4)
    save(fig, "fig2_qc_2024_25.svg")


def fig3_coverage() -> None:
    mc = pd.read_csv(RESULTS / "model_comparison.csv")
    methods = [("lightgbm", "LightGBM"), ("negbin", "Negative\nbinomial"), ("random_forest", "Random\nforest"),
               ("sarimax", "SARIMAX")]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    for i, (key, _) in enumerate(methods):
        d = mc[mc.model == key].reset_index(drop=True)
        jitter = (d.index % 8 - 3.5) * 0.022
        ax.scatter(i - 0.17 + jitter, 100 * d.coverage_raw, s=11, color=ORANGE, alpha=0.85, lw=0,
                   label="Before calibration" if i == 0 else None)
        ax.scatter(i + 0.17 + jitter, 100 * d.coverage_10_90, s=11, color=BLUE, alpha=0.85, lw=0,
                   label="After calibration" if i == 0 else None)
    ax.axhline(80, color=INK2, lw=0.9, ls=(0, (4, 3)))
    ax.text(3.55, 80.8, "80% target", fontsize=7.5, color=INK2, ha="right", va="bottom")
    ax.set_xticks(range(len(methods)), [m[1] for m in methods])
    ax.set_xlim(-0.6, 3.6)
    ax.set_ylabel("Real weeks inside the range (%)")
    ax.set_ylim(40, 100)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower right", fontsize=7.5, ncols=2)
    fig.tight_layout()
    save(fig, "fig3_coverage.svg")


def fig4_weather() -> None:
    fg = pd.read_csv(RESULTS / "feature_groups.csv")
    add = fg[(fg["mode"] == "add") & fg.group.isin(["rain", "heat", "humidity"])]
    med = add.groupby(["panel", "group", "horizon"]).change_pct.median()
    series = [("rain", "Rain", BLUE), ("heat", "Heat", ORANGE), ("humidity", "Humidity", GREEN)]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), sharey=True)
    for ax, (panel, title) in zip(axes, [("region_qc", "Regions + Quezon City (16 checks)"),
                                         ("province", "Provinces (8 checks)")]):
        ax.axhline(0, color=MUTED, lw=0.8)
        for key, label, color in series:
            s = med.loc[(panel, key)]
            ax.plot(s.index, s.values, color=color, lw=1.6, marker="o", ms=3.5, label=label)
        ax.set_title(title)
        ax.set_xticks([2, 4, 6, 8])
        ax.set_xlabel("Weeks ahead")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Median change in error (%)")
    axes[0].legend(loc="lower left", fontsize=7.5)
    fig.tight_layout()
    save(fig, "fig4_weather_by_lead.svg")


MATH = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$", re.S)


def to_html(md_text: str) -> str:
    stash: list[str] = []

    def keep(m: re.Match) -> str:
        stash.append(m.group(0))
        return f"@@MATH{len(stash) - 1}@@"

    body = markdown.markdown(MATH.sub(keep, md_text), extensions=["tables"])
    body = re.sub(r"@@MATH(\d+)@@", lambda m: htmllib.escape(stash[int(m.group(1))], quote=False), body)

    def inline_svg(m: re.Match) -> str:  # embed figures so the PDF needs no file access
        data = base64.b64encode((HERE / m.group(2)).read_bytes()).decode()
        return f'<img alt="{m.group(1)}" src="data:image/svg+xml;base64,{data}">'

    body = re.sub(r'<img alt="([^"]*)" src="([^"]+\.svg)"\s*/?>', inline_svg, body)
    body = re.sub(r"<p><img", '<p class="fig"><img', body)
    body = re.sub(r"<p><strong>(Figure|Table) (\d+)\.</strong>", r'<p class="cap"><strong>\1 \2.</strong>', body)
    body = re.sub(r"<p><em>Note\.</em>", '<p class="note"><em>Note.</em>', body)
    return body


CSS = """
@page { size: A4; }
:root { --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781; --grid: #e1e0d9; }
body { margin: 0; font-family: Cambria, Georgia, "Times New Roman", serif; font-size: 10.4pt; line-height: 1.5;
       color: var(--ink); text-align: justify; hyphens: auto; }
h1 { font-size: 17pt; line-height: 1.25; text-align: left; margin: 0 0 10pt; }
h1 + p { text-align: left; margin-bottom: 2pt; }
h2 { font-size: 13pt; margin: 18pt 0 6pt; text-align: left; break-after: avoid; }
h3 { font-size: 11pt; margin: 13pt 0 4pt; text-align: left; break-after: avoid; }
h4 { font-size: 10.4pt; font-style: italic; font-weight: normal; margin: 10pt 0 3pt; break-after: avoid; }
p { margin: 0 0 7pt; }
hr { border: 0; border-top: 0.75px solid var(--grid); margin: 12pt 0; }
ol, ul { margin: 0 0 7pt; padding-left: 18pt; }
li { margin-bottom: 2pt; }
code { font-family: Consolas, monospace; font-size: 8.8pt; color: var(--ink-2); }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 4pt; font-family: "Segoe UI", Arial, sans-serif;
        font-size: 7.6pt; line-height: 1.3; text-align: left; break-inside: avoid; }
th { border-top: 1.2px solid var(--ink); border-bottom: 0.75px solid var(--ink); padding: 3pt 4pt;
     vertical-align: bottom; font-weight: 600; }
td { padding: 2.5pt 4pt; border-bottom: 0.5px solid var(--grid); vertical-align: top; }
tr:last-child td { border-bottom: 1.2px solid var(--ink); }
p.cap { font-size: 9pt; line-height: 1.4; text-align: left; margin: 10pt 0 3pt; break-after: avoid; }
p.fig + p.cap { margin-top: 2pt; }
p.note { font-size: 8.4pt; line-height: 1.35; color: var(--ink-2); text-align: left; }
p.fig { text-align: center; margin: 10pt 0 0; break-inside: avoid; break-after: avoid; }
p.fig img { width: 100%; }
.katex { font-size: 1.02em; }
.katex-display { margin: 6pt 0 8pt; }
h2#references ~ p { font-size: 8.8pt; line-height: 1.4; text-align: left; padding-left: 14pt; text-indent: -14pt;
                    margin-bottom: 4pt; }
"""


# on a screen (the website's reader, scripts/research_docs.py): a readable column that also fits a phone
SCREEN_CSS = """
@media screen {
  html { background: #f3f2ea; }
  body { max-width: 760px; margin: 0 auto; padding: 32px 36px 56px; background: #fff; font-size: 16px; }
  h1 { font-size: 27px; } h2 { font-size: 21px; } h3 { font-size: 17px; } h4 { font-size: 16px; }
  table { font-size: 12.5px; display: block; overflow-x: auto; }
  p.cap { font-size: 14px; } p.note { font-size: 13px; } h2#references ~ p { font-size: 14px; overflow-wrap: anywhere; }
  .katex-display { overflow-x: auto; overflow-y: hidden; }
}
@media screen and (max-width: 640px) { body { padding: 20px 16px 36px; font-size: 15px; text-align: left; } }
"""


def page_html(screen: bool = False) -> str:
    """The paper as one HTML page: KaTeX typesets the math, the figures are inlined."""
    body = to_html((HERE / "paper.md").read_text(encoding="utf-8"))
    body = body.replace("<h2>References</h2>", '<h2 id="references">References</h2>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<script src="{KATEX}/katex.min.js"></script><script src="{KATEX}/contrib/auto-render.min.js"></script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EpiLag-PH research paper</title>
<style>{CSS}{SCREEN_CSS if screen else ""}</style></head><body>{body}
<script>
renderMathInElement(document.body, {{delimiters: [{{left: "$$", right: "$$", display: true}},
  {{left: "$", right: "$", display: false}}], throwOnError: true}});
document.fonts.ready.then(() => document.body.dataset.ready = "1");
</script></body></html>"""


def build_pdf() -> None:
    footer = ('<div style="width:100%;font:7.5pt Segoe UI,sans-serif;color:#898781;padding:0 16mm;'
              'display:flex;justify-content:space-between"><span>EpiLag-PH · PJDSC 2026</span>'
              '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(page_html(), wait_until="networkidle")
        page.wait_for_selector("body[data-ready='1']", timeout=30000)
        if page.locator(".katex-error").count():
            raise SystemExit("KaTeX could not typeset some math")
        page.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
                 header_template="<span></span>", footer_template=footer,
                 margin={"top": "18mm", "bottom": "18mm", "left": "20mm", "right": "20mm"})
        browser.close()


def main() -> None:
    FIG.mkdir(exist_ok=True)
    fig1_weekly_cases()
    fig2_qc()
    fig3_coverage()
    fig4_weather()
    build_pdf()
    print(f"wrote {OUT.relative_to(ROOT)} and 4 figures in {FIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
