"""Build research/EpiLag-PH-research-summary.pdf from research/writeup/summary.html.

The two data charts are drawn here from the result CSVs and dropped into the HTML's {{chart_*}} slots;
the rest of the text and tables are in summary.html. Needs Playwright with Chromium (`playwright install chromium`).
Usage: python research/writeup/build_summary.py
"""
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
HTML = Path(__file__).with_name("summary.html")
OUT = ROOT / "research" / "EpiLag-PH-research-summary.pdf"

INK, INK2, MUTED, GRID, BASE, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
SERIES = {"rain": ("Rain", "#2a78d6"), "heat": ("Heat (temperature)", "#eb6834"), "humidity": ("Humidity", "#1baf7a")}
HORIZONS = [2, 4, 6, 8]


def spread(ys: list[float], gap: float = 11) -> list[float]:
    """Push label positions apart so no two are closer than `gap` px, keeping their order."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    out = list(ys)
    for a, b in zip(order, order[1:]):
        out[b] = max(out[b], out[a] + gap)
    return out


def weather_chart() -> str:
    """Small multiples: median error change from adding each weather group to cases + season, by lead time."""
    fg = pd.read_csv(RESULTS / "feature_groups.csv")
    add = fg[(fg["mode"] == "add") & fg.group.isin(SERIES)]
    med = add.pivot_table(index=["panel", "group"], columns="horizon", values="change_pct", aggfunc="median")
    lo, hi, top, h = -8, 3, 28, 160
    y = lambda v: top + (hi - v) / (hi - lo) * h
    parts = []
    for i, (panel, title) in enumerate([("region_qc", "Regions + QC"), ("province", "Provinces")]):
        x0 = 6 + i * 322
        px = lambda k: x0 + 40 + k * 64
        parts.append(f'<text x="{x0 + 40}" y="14" font-size="11" font-weight="600" fill="{INK}">{title}</text>')
        for v in range(-8, 3, 2):
            stroke, w = (BASE, 1.2) if v == 0 else (GRID, 1)
            parts.append(f'<line x1="{x0 + 40}" x2="{px(3)}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{stroke}" stroke-width="{w}"/>')
            parts.append(f'<text x="{x0 + 32}" y="{y(v) + 3.5:.1f}" font-size="9" fill="{MUTED}" text-anchor="end">{v:+d}%</text>'.replace("+0%", "0%"))
        for k, hz in enumerate(HORIZONS):
            parts.append(f'<text x="{px(k)}" y="{top + h + 15}" font-size="9" fill="{MUTED}" text-anchor="middle">{hz}</text>')
        parts.append(f'<text x="{px(1.5)}" y="{top + h + 29}" font-size="9" fill="{INK2}" text-anchor="middle">weeks ahead</text>')
        ends = []
        for g, (label, colour) in SERIES.items():
            vals = [med.loc[(panel, g), hz] for hz in HORIZONS]
            pts = " ".join(f"{px(k):.1f},{y(v):.1f}" for k, v in enumerate(vals))
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2" stroke-linejoin="round"/>')
            parts += [f'<circle cx="{px(k):.1f}" cy="{y(v):.1f}" r="4" fill="{colour}" stroke="{SURFACE}" stroke-width="2"/>'
                      for k, v in enumerate(vals)]
            ends.append((y(vals[-1]), f"{label.split(' ')[0]} {vals[-1]:+.1f}%".replace("-", "&minus;")))
        for ly, (_, text) in zip(spread([e[0] for e in ends]), ends):
            parts.append(f'<text x="{px(3) + 9}" y="{ly + 3.5:.1f}" font-size="9" fill="{INK}">{text}</text>')
    legend = "".join(f'<span><i style="background:{c}"></i>{l}</span>' for l, c in SERIES.values())
    return (f'<figure><figcaption>Weather&rsquo;s value grows with lead time for Regions + QC, not for provinces '
            f'<span>&middot; median change in error when the group is added to recent cases + season; below zero is better</span></figcaption>'
            f'<div class="legend">{legend}</div>'
            f'<svg viewBox="0 0 650 222" width="100%" role="img" aria-label="Median error change by lead time for rain, heat and humidity, '
            f'Regions + QC and provinces">{"".join(parts)}</svg>'
            f'<p class="src">Source: <code>research/results/feature_groups.csv</code> (mode <code>add</code>); '
            f'16 checks for Regions + QC, 8 for provinces. Labels give the 8-week value.</p></figure>')


def coverage_chart() -> str:
    """Range bars: share of weeks inside the 10-90% range, min to max over 24 checks, before and after calibration."""
    mc = pd.read_csv(RESULTS / "model_comparison.csv")
    methods = [("lightgbm", "LightGBM"), ("negbin", "Negative binomial"), ("random_forest", "Random forest"), ("sarimax", "SARIMAX")]
    kinds = [("coverage_raw", "Before calibration", "#2a78d6", -7), ("coverage_10_90", "After calibration", "#eb6834", 7)]
    x = lambda v: 140 + (v - 0.4) / 0.6 * 470
    top, row = 26, 40
    parts = []
    for v in range(40, 101, 10):
        parts.append(f'<line x1="{x(v / 100):.1f}" x2="{x(v / 100):.1f}" y1="{top - 6}" y2="{top + 4 * row - 6}" stroke="{GRID}"/>')
        parts.append(f'<text x="{x(v / 100):.1f}" y="{top + 4 * row + 8}" font-size="9" fill="{MUTED}" text-anchor="middle">{v}%</text>')
    t = x(0.8)
    parts.append(f'<line x1="{t:.1f}" x2="{t:.1f}" y1="{top - 12}" y2="{top + 4 * row - 6}" stroke="{INK2}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    parts.append(f'<text x="{t:.1f}" y="{top - 16}" font-size="9" fill="{INK2}" text-anchor="middle">target 80%</text>')
    for i, (m, name) in enumerate(methods):
        g = mc[mc.model == m]
        cy = top + i * row + 12
        parts.append(f'<text x="0" y="{cy + 4}" font-size="10" fill="{INK}" font-weight="600">{name}</text>')
        for col, _, colour, dy in kinds:
            lo, hi, mean = g[col].min(), g[col].max(), g[col].mean()
            parts.append(f'<line x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="{cy + dy}" y2="{cy + dy}" stroke="{colour}" stroke-width="6" stroke-linecap="round"/>')
            parts.append(f'<circle cx="{x(mean):.1f}" cy="{cy + dy}" r="4.5" fill="{INK}" stroke="{SURFACE}" stroke-width="2"/>')
            if m == "lightgbm":
                parts.append(f'<text x="{x(hi) + 8:.1f}" y="{cy + dy + 3.5}" font-size="9" fill="{INK}">{lo:.0%}&ndash;{hi:.0%}</text>')
    legend = "".join(f'<span><i style="background:{c}; height:6px"></i>{l}</span>' for _, l, c, _ in kinds)
    legend += f'<span><i class="sw" style="background:{INK}; border-radius:50%; width:8pt; height:8pt"></i>Mean</span>'
    return (f'<figure><figcaption>Calibration brings every method&rsquo;s range close to 80% '
            f'<span>&middot; share of weeks inside the 10&ndash;90% range, lowest to highest of 24 checks</span></figcaption>'
            f'<div class="legend">{legend}</div>'
            f'<svg viewBox="0 0 650 {top + 4 * row + 14}" width="100%" role="img" aria-label="Range held before and after calibration, '
            f'per method">{"".join(parts)}</svg></figure>')


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    html = html.replace("{{chart_weather}}", weather_chart()).replace("{{chart_coverage}}", coverage_chart())
    assert "{{" not in html, "unfilled chart slot"
    footer = ('<div style="font-family:Segoe UI,sans-serif;font-size:7.5pt;color:#898781;width:100%;padding:0 16mm;'
              'display:flex;justify-content:space-between"><span>EpiLag-PH research summary &middot; PJDSC 2026</span>'
              '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(path=str(OUT), format="A4", print_background=True, display_header_footer=True,
                 header_template="<span></span>", footer_template=footer,
                 margin={"top": "15mm", "bottom": "17mm", "left": "16mm", "right": "16mm"})
        browser.close()
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
