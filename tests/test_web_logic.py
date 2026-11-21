"""Parity: the JavaScript web app (docs/web/) computes what the Python app computes, on the same data.

Serves the built docs/ (run `cd site && npm run build` and `python scripts/build_web.py` first), opens the app in
Playwright, calls its logic module through `page.evaluate` (window.epilag.logic), and compares with Python on the
same JSON the app loads:
  - alert levels for every forecast row (app/streamlit_app.py alert_level, read from the app source)
  - thresholds (src/thresholds.py), replay forecasts and the "30 of 32" claim (replay_forecast in the app)
  - the budget plan (src/allocate.py) across budgets of PHP 0.5M-20M
  - the alert track record per area (src/reliability.py), latest and as a replay sees it
  - the overview's "Rising toward an outbreak" list (src/thresholds.py line_share)
  - the one-SMS resident message: every level, language and area fits in 160 GSM-7 characters
Skipped when Playwright or the built app is missing.
"""
import ast
import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = DOCS / "web" / "data"
sys.path.insert(0, str(ROOT / "src"))
from allocate import Action, allocate  # noqa: E402
from thresholds import line_share, thresholds  # noqa: E402
from reliability import track_record  # noqa: E402

playwright = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not (DOCS / "web" / "index.html").exists() or not (DATA / "meta.json").exists(),
                                reason="build the web app first (npm run build, scripts/build_web.py)")
LEVELS = ["normal", "above usual", "watch", "outbreak warning"]


def _app_function(name: str):
    """A function from app/streamlit_app.py, compiled on its own (the app module itself needs Streamlit)."""
    tree = ast.parse((ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    ns = {"pd": pd, "LEVELS": LEVELS}
    exec(compile(ast.Module([node], []), "streamlit_app.py", "exec"), ns)  # noqa: S102
    return ns[name]


alert_level = _app_function("alert_level")


# ------------------------------------------------------------------ the same data the app loads, as DataFrames
def _frame(panel: str, name: str) -> pd.DataFrame:
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))["panels"][panel]
    t = json.loads((DATA / f"{panel}_{name}.json").read_text(encoding="utf-8"))
    df = pd.DataFrame({("unit_id" if k == "u" else k): v for k, v in t["cols"].items()})
    df["unit_id"] = [meta["units"][i] for i in df.unit_id]
    for c in ("week", "target_week"):
        if c in df:
            df[c] = pd.to_datetime(df[c], unit="D")
    for c in df.columns:
        if c not in ("unit_id", "level", "driver", "week", "target_week") and df[c].dtype == object:
            df[c] = df[c].astype(float)
    return df


def _meta(panel):
    return json.loads((DATA / "meta.json").read_text(encoding="utf-8"))["panels"][panel]


def replay_forecast_py(panel: str, origin: pd.Timestamp) -> pd.DataFrame:
    """replay_forecast() of app/streamlit_app.py on the exported data."""
    m = _meta(panel)
    b = _frame(panel, "backtest")
    b = b.assign(origin=b.target_week - pd.to_timedelta(b.horizon * 7, unit="D"))
    f = b[b.origin == origin].copy()
    f = f[f.unit_id.isin(set(_frame(panel, "forecast").unit_id))]
    f["population"] = f.unit_id.map(m["population"])
    f["woy"] = f.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
    hist = _frame(panel, "history")
    thr = thresholds(hist[hist.week < f"{origin.year}-01-01"])
    f = f.merge(thr, on=["unit_id", "woy"], how="left")
    f["level"] = alert_level(f.q50, f.q90, f.alert, f.epidemic)
    f["actual_level"] = alert_level(f.actual, f.actual, f.alert, f.epidemic)
    f["q50_per100k"] = f.q50 / f.population * 1e5
    return f


# ------------------------------------------------------------------ the app in a browser
class _Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):  # the site is published under /epilag/
        return super().translate_path(path.removeprefix("/epilag"))

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def page():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Handler, directory=str(DOCS)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:  # noqa: BLE001 (no Chrome installed: use Playwright's own Chromium)
            browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(f"http://127.0.0.1:{server.server_address[1]}/epilag/web/?page=about")
        pg.wait_for_function("window.epilag && window.epilag.logic")
        yield pg
        browser.close()
    server.shutdown()


def days(ts: pd.Timestamp) -> int:
    return int((ts - pd.Timestamp("1970-01-01")).days)


# ------------------------------------------------------------------ tests
@pytest.mark.parametrize("panel", ["region_qc", "province"])
def test_alert_level_matches(page, panel):
    fc = _frame(panel, "forecast")
    py = alert_level(fc.q50, fc.q90, fc.alert, fc.epidemic).tolist()
    js = page.evaluate("rows => rows.map(r => window.epilag.logic.alertLevel(r[0], r[1], r[2], r[3]))",
                       fc[["q50", "q90", "alert", "epidemic"]].values.tolist())
    assert js == py
    # and the published levels survive the 4-significant-digit rounding of the export
    assert (fc.level == pd.Series(py)).mean() > 0.97


@pytest.mark.parametrize("panel", ["region_qc", "province"])
def test_thresholds_match(page, panel):
    hist = _frame(panel, "history")
    py = thresholds(hist[hist.week < "2019-01-01"]).set_index(["unit_id", "woy"])
    js = page.evaluate("""async ([panel, cut]) => {
        const l = window.epilag.logic, h = await window.epilag.data.table(panel, "history");
        return [...l.thresholds(h.filter(r => r.week < cut))].map(([k, v]) => [k, v.alert, v.epidemic]); }""",
                       [panel, days(pd.Timestamp("2019-01-01"))])
    assert len(js) == len(py)
    for key, a, e in js:
        u, w = key.split("|")
        r = py.loc[(u, int(w))]
        assert a == pytest.approx(r.alert, rel=1e-9, abs=1e-9)
        assert e == pytest.approx(r.epidemic, rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("panel,origin", [("province", "2019-06-02"), ("province", "2020-02-02"),
                                          ("region_qc", "2019-06-02"), ("region_qc", "2024-02-04")])
def test_replay_matches(page, panel, origin):
    o = pd.Timestamp(origin)
    py = replay_forecast_py(panel, o).sort_values(["unit_id", "horizon"]).reset_index(drop=True)
    js = pd.DataFrame(page.evaluate("""async ([panel, origin]) => {
        const d = window.epilag.data; return await d.forecastFor({ panel, mode: "replay", origin }); }""",
                                    [panel, days(o)])).sort_values(["unit_id", "horizon"]).reset_index(drop=True)
    assert len(js) == len(py) > 0
    assert js.unit_id.tolist() == py.unit_id.tolist()
    assert js.level.tolist() == py.level.tolist()
    assert js.actual_level.tolist() == py.actual_level.tolist()
    assert js.q50_per100k.tolist() == pytest.approx(py.q50_per100k.tolist(), rel=1e-9)


@pytest.mark.parametrize("h", [4, 8])
def test_replay_claim_june_2019(page, h):
    """The README claim: provinces that crossed the epidemic line, and how many were flagged in advance."""
    py = replay_forecast_py("province", pd.Timestamp("2019-06-02"))
    py = py[py.horizon == h]
    crossed = py[py.actual_level == LEVELS[3]]
    flagged = int(crossed.level.isin(LEVELS[2:]).sum())
    js = page.evaluate("""async ([origin, h]) => {
        const rows = await window.epilag.data.forecastFor({ panel: "province", mode: "replay", origin });
        return window.epilag.logic.replayClaim(rows.filter(r => r.horizon === h)); }""",
                       [days(pd.Timestamp("2019-06-02")), h])
    assert js == {"crossed": len(crossed), "flagged": flagged}
    if h == 4:
        assert (js["flagged"], js["crossed"]) == (30, 32)


@pytest.mark.parametrize("panel", ["region_qc", "province"])
@pytest.mark.parametrize("budget", [500_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000])
def test_allocate_matches(page, panel, budget):
    m = _meta(panel)
    fc = _frame(panel, "forecast")
    fc["unit_name"] = fc.unit_id.map(m["names"])
    fc["population"] = fc.unit_id.map(m["population"])
    py = allocate(fc[fc.horizon.isin([2, 4, 6, 8])], budget)
    js = pd.DataFrame(page.evaluate("""async ([panel, budget]) => {
        const d = window.epilag.data, rows = await d.forecastFor({ panel, mode: "latest" });
        return window.epilag.logic.allocate(rows.filter(r => [2, 4, 6, 8].includes(r.horizon)), budget); }""",
                                    [panel, budget]), columns=py.columns)
    assert list(zip(js.unit_id, js.action)) == list(zip(py.unit_id, py.action))
    for c in ("spend", "people_covered", "averted_low", "averted_mid", "averted_high"):
        assert js[c].tolist() == pytest.approx(py[c].tolist(), rel=1e-9, abs=1e-6)
    assert js.spend.sum() == pytest.approx(min(budget, py.spend.sum()), rel=1e-9)


@pytest.mark.parametrize("panel", ["region_qc", "province"])
@pytest.mark.parametrize("priority", ["level", "value"])
@pytest.mark.parametrize("budget", [5_000_000, 1e9])
def test_allocate_by_level_matches(page, panel, priority, budget):
    # Mixed levels, so some areas are cut off from fogging: the same lines come out of both apps.
    m = _meta(panel)
    fc = _frame(panel, "forecast")
    fc["unit_name"] = fc.unit_id.map(m["names"])
    fc["population"] = fc.unit_id.map(m["population"])
    levels = {u: LEVELS[i % 4] for i, u in enumerate(sorted(fc.unit_id.unique()))}
    py = allocate(fc[fc.horizon.isin([2, 4, 6, 8])], budget, levels=levels, priority=priority)
    if budget == 1e9:
        assert set(py.action) == {"Clean-up drive + container covers", "Targeted fogging"}
    assert (py[py.action == "Targeted fogging"].unit_id.map(levels).map(LEVELS.index) >= 2).all()
    js = pd.DataFrame(page.evaluate("""async ([panel, levels, budget, priority]) => {
        const rows = await window.epilag.data.forecastFor({ panel, mode: "latest" });
        return window.epilag.logic.allocate(rows.filter(r => [2, 4, 6, 8].includes(r.horizon)), budget, undefined, levels, priority); }""",
                                    [panel, levels, budget, priority]), columns=py.columns)
    assert list(zip(js.unit_id, js.action)) == list(zip(py.unit_id, py.action))
    assert js.averted_mid.tolist() == pytest.approx(py.averted_mid.tolist(), rel=1e-9)


def test_allocate_custom_actions(page):
    actions = (Action("a", 12.0, 0.05, 0.2, 0.4, 0.25), Action("b", 30.0, 0.0, 0.1, 0.2, 0.15))
    m = _meta("region_qc")
    fc = _frame("region_qc", "forecast")
    fc["unit_name"] = fc.unit_id.map(m["names"])
    fc["population"] = fc.unit_id.map(m["population"])
    py = allocate(fc, 3_000_000, actions)
    js = page.evaluate("""async (acts) => {
        const rows = await window.epilag.data.forecastFor({ panel: "region_qc", mode: "latest" });
        return window.epilag.logic.allocate(rows, 3000000, acts); }""",
                       [dict(name=a.name, cost_per_person=a.cost_per_person, effect_low=a.effect_low,
                             effect_central=a.effect_central, effect_high=a.effect_high, max_coverage=a.max_coverage)
                        for a in actions])
    assert [r["averted_mid"] for r in js] == pytest.approx(py.averted_mid.tolist(), rel=1e-9)


@pytest.mark.parametrize("panel,h,before", [("region_qc", 4, None), ("region_qc", 8, None), ("province", 4, None),
                                            ("province", 8, None), ("region_qc", 4, 2024), ("province", 4, 2020)])
def test_track_record_matches(page, panel, h, before):
    py = track_record(_frame(panel, "history"), _frame(panel, "backtest"), h, before).set_index("unit_id")
    js = page.evaluate("""async ([panel, h, before]) => {
        const d = window.epilag.data, [hist, bt] = await Promise.all([d.table(panel, "history"), d.table(panel, "backtest")]);
        return [...window.epilag.logic.trackRecord(hist, bt, h, before)].map(([u, r]) => ({ unit_id: u, ...r, years: r.years.join(",") })); }""",
                       [panel, h, before])
    assert len(js) == len(py) > 0
    for r in js:
        p = py.loc[r["unit_id"]]
        for k in ("alert_weeks", "alert_weeks_right", "onsets", "onsets_caught"):
            assert r[k] == p[k], (r["unit_id"], k)
        assert r["grade"] == p.grade and r["years"] == p.years
        assert (r["reliability"] is None) == pd.isna(p.reliability)


def test_track_record_replay_uses_only_earlier_years(page):
    """A 2019 replay has no earlier test year, so no track record; a 2020 replay uses 2019 only."""
    out = page.evaluate("""async () => {
        const d = window.epilag.data;
        const r19 = await d.trackRecordFor({ panel: "province", mode: "replay", origin: 18049, horizon: 4 });
        const r20 = await d.trackRecordFor({ panel: "province", mode: "replay", origin: 18294, horizon: 4 });
        return [r19.size, [...new Set([...r20.values()].flatMap((r) => r.years))]]; }""")
    assert out == [0, [2019]]


def test_report_card_ranges(page):
    """Report card cells say where the reported cases fell against the 10-90% range of the forecast."""
    rc = page.evaluate("""async () => {
        const d = window.epilag.data, [hist, bt] = await Promise.all([d.table("region_qc", "history"), d.table("region_qc", "backtest")]);
        return window.epilag.logic.reportCard(bt, hist, 4, 8); }""")
    assert len(rc["weeks"]) == 8 and len(rc["rows"]) == 18
    for row in rc["rows"]:
        for c in row["cells"]:
            want = 1 if c["actual"] > c["q90"] else -1 if c["actual"] < c["q10"] else 0
            assert c["hit"] == want
        assert row["inside"] == sum(c["hit"] == 0 for c in row["cells"])


GSM7 = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")


def test_sms_fits_one_message(page):
    names = sorted({n for p in ("region_qc", "province") for n in _meta(p)["names"].values()}, key=len)
    msgs = page.evaluate("""async (names) => {
        const res = [];
        for (const lang of ["en", "fil"]) {
          for (const lv of ["outbreak warning", "watch", "above usual", "normal"]) {
            const tpl = window.epilag.labels[lang].sms[lv];
            for (const n of names) for (const h of [2, 4, 6, 8]) res.push(window.epilag.logic.smsText(tpl, n, h));
          }
        }
        return res; }""", names)
    assert len(msgs) == 2 * 4 * len(names) * 4
    for m in msgs:
        assert len(m) <= 160, m
        assert set(m) <= GSM7, set(m) - GSM7
    # the longest real name fits without being shortened
    assert any(names[-1] in m for m in msgs)


@pytest.mark.parametrize("panel,h", [("region_qc", 4), ("region_qc", 8), ("province", 4), ("province", 8)])
def test_rising_toward_matches(page, panel, h):
    """Each area's latest week and forecast, as a share of the way from its usual level to its outbreak line."""
    fc = _frame(panel, "forecast")
    fc = fc[fc.horizon == h].copy()
    as_of = fc.week.max()
    hist = _frame(panel, "history")
    now = hist[(hist.week == as_of) & hist.cases.notna()].set_index("unit_id").cases
    thr = _frame(panel, "thresholds").set_index(["unit_id", "woy"])
    w = min(int(as_of.isocalendar().week), 52)
    fc = fc[fc.unit_id.isin(now.index)]
    fc["now"] = fc.unit_id.map(now)
    t = thr.loc[[(u, w) for u in fc.unit_id]]
    fc["from_"] = line_share(fc.now.values, t.alert.values, t.epidemic.values)
    fc["to"] = line_share(fc.q50, fc.alert, fc.epidemic)
    py = fc[(fc.to > 0) & (fc.to > fc.from_)].assign(rise=lambda d: d.to - d.from_)
    py = py.sort_values(["to", "rise"], ascending=False).head(5)
    js = page.evaluate("""async ([panel, h]) => {
        const l = window.epilag.logic, d = window.epilag.data;
        const fc = (await d.table(panel, "forecast")).filter(r => r.horizon === h);
        const asOf = Math.max(...fc.map(r => r.week));
        const now = new Map((await d.table(panel, "history")).filter(r => r.week === asOf && r.cases != null).map(r => [r.unit_id, r.cases]));
        const thr = new Map((await d.table(panel, "thresholds")).map(r => [`${r.unit_id}|${r.woy}`, r]));
        return l.risingToward(fc, now, thr).map(r => [r.unit_id, r.from, r.to]); }""", [panel, h])
    assert [u for u, _, _ in js] == py.unit_id.tolist()
    for (_, f, to), (_, r) in zip(js, py.iterrows()):
        assert f == pytest.approx(r.from_, rel=1e-9, abs=1e-9)
        assert to == pytest.approx(r.to, rel=1e-9, abs=1e-9)
