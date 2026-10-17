"""EpiLag-PH: climate-informed dengue early warning for Philippine LGUs."""
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP = Path(__file__).resolve().parent
DATA = APP / "data"
sys.path.insert(0, str(APP.parent / "src"))
from allocate import Action, allocate  # noqa: E402

st.set_page_config(page_title="EpiLag-PH", layout="wide")

LEVELS = ["normal", "above usual", "watch", "outbreak warning"]
LEVEL_COLOR = {"normal": "#CBD2D9", "above usual": "#F5D78E", "watch": "#F0A04B", "outbreak warning": "#C8372D"}
ACCENT, MUTED, BAND = "#0F766E", "#7B8794", "rgba(15,118,110,0.18)"

PANELS = {
    "region_qc": {"label": {"en": "Regions + Quezon City (latest data: Dec 2025)",
                            "fil": "Mga rehiyon + Quezon City (pinakabagong datos: Dis 2025)"},
                  "geo": "region.geojson"},
    "province": {"label": {"en": "Provinces (historical replay: Jan 2021)",
                           "fil": "Mga lalawigan (pagbabalik-tanaw: Ene 2021)"},
                 "geo": "province.geojson"},
}

T = {
    "en": {
        "tagline": "Dengue early warning from rain, heat and recent cases. Act weeks before hospitals fill.",
        "nav_map": "Forecast map", "nav_unit": "Area detail", "nav_proof": "Did it work?",
        "nav_budget": "Budget plan", "nav_qc": "Quezon City barangays", "nav_about": "Data & limits",
        "dataset": "Data", "horizon": "Weeks ahead", "lang": "Language",
        "mode": "Forecast", "mode_latest": "Latest", "mode_replay": "Replay a past week",
        "origin": "Forecast made in the week ending", "actual_col": "What happened",
        "replay_note": ("Replay: these forecasts were made by models trained only on earlier years, "
                        "so they show what EpiLag would have said at the time."),
        "hits": "Areas that actually crossed the epidemic threshold", "caught": "flagged in advance (watch or warning)",
        "as_of": "Forecast made from the week ending", "for_week": "for the week ending",
        "warning_n": "Outbreak warning", "watch_n": "Watch", "above_n": "Above usual", "normal_n": "Normal",
        "rank": "Areas ranked by forecast cases per 100,000", "area": "Area", "level": "Alert level",
        "cases": "Forecast cases", "range": "Likely range", "per100k": "Per 100,000",
        "pick": "Choose an area", "history": "Weekly cases, forecasts and thresholds",
        "actual": "Reported cases", "fc4": "Forecast made 4 weeks earlier", "fcnow": "Latest forecast",
        "epi_line": "Epidemic threshold", "why": "Why this forecast",
        "why_note": "Contribution to the forecast (log scale). Positive pushes the forecast up.",
        "budget": "Budget (PHP)", "cost": "Cost per person covered (PHP, example value)",
        "effect": "Effect on cases: low / central / high", "plan": "Funded actions",
        "averted": "Cases averted in 8 weeks (low / central / high)",
        "qc_head": "Quezon City: where to look first",
        "qc_note": ("Weekly forecasts are city-wide. Barangay data is yearly only, so the city forecast "
                    "is shared out by each barangay's share of cases in 2022-2025."),
    },
    "fil": {
        "tagline": "Maagang babala sa dengue mula sa ulan, init at mga bagong kaso. Kumilos bago mapuno ang ospital.",
        "nav_map": "Mapa ng forecast", "nav_unit": "Detalye ng lugar", "nav_proof": "Gumana ba?",
        "nav_budget": "Plano ng budget", "nav_qc": "Mga barangay ng Quezon City", "nav_about": "Datos at limitasyon",
        "dataset": "Datos", "horizon": "Ilang linggo pa", "lang": "Wika",
        "mode": "Forecast", "mode_latest": "Pinakabago", "mode_replay": "Balikan ang nakaraang linggo",
        "origin": "Forecast na ginawa sa linggong nagtapos noong", "actual_col": "Ang nangyari",
        "replay_note": ("Pagbabalik-tanaw: ginawa ang mga forecast na ito ng modelong sinanay lamang sa mga naunang "
                        "taon, kaya ipinapakita nito ang sasabihin sana ng EpiLag noon."),
        "hits": "Mga lugar na talagang lumampas sa threshold ng epidemya", "caught": "nababalaan nang maaga (bantayan o babala)",
        "as_of": "Forecast mula sa linggong nagtapos noong", "for_week": "para sa linggong magtatapos sa",
        "warning_n": "Babala ng outbreak", "watch_n": "Bantayan", "above_n": "Mas mataas sa karaniwan", "normal_n": "Normal",
        "rank": "Mga lugar ayon sa forecast na kaso bawat 100,000", "area": "Lugar", "level": "Antas ng babala",
        "cases": "Forecast na kaso", "range": "Malamang na saklaw", "per100k": "Bawat 100,000",
        "pick": "Pumili ng lugar", "history": "Lingguhang kaso, forecast at threshold",
        "actual": "Naiulat na kaso", "fc4": "Forecast 4 na linggo bago", "fcnow": "Pinakabagong forecast",
        "epi_line": "Threshold ng epidemya", "why": "Bakit ganito ang forecast",
        "why_note": "Ambag sa forecast (log scale). Positibo = nagpapataas ng forecast.",
        "budget": "Budget (PHP)", "cost": "Gastos bawat taong maaabot (PHP, halimbawa lamang)",
        "effect": "Epekto sa kaso: mababa / gitna / mataas", "plan": "Mga gawaing popondohan",
        "averted": "Kasong maiiwasan sa 8 linggo (mababa / gitna / mataas)",
        "qc_head": "Quezon City: saan unang titingin",
        "qc_note": ("Ang lingguhang forecast ay para sa buong lungsod. Taunan lang ang datos ng barangay, kaya "
                    "hinati ang forecast ayon sa bahagi ng bawat barangay sa mga kaso noong 2022-2025."),
    },
}

ALERT_TEXT = {
    "en": {
        "outbreak warning": "Outbreak warning: cases are forecast above the epidemic threshold. Start clean-up drives now, pre-position test kits, and alert hospitals.",
        "watch": "Watch: an outbreak is possible. Check breeding sites this week and prepare teams.",
        "above usual": "Above usual: cases are forecast higher than normal for this time of year. Keep watch.",
        "normal": "Normal: no unusual rise expected.",
    },
    "fil": {
        "outbreak warning": "Babala ng outbreak: inaasahang lalampas ang kaso sa threshold ng epidemya. Simulan na ang paglilinis, ihanda ang test kits, at abisuhan ang mga ospital.",
        "watch": "Bantayan: posible ang outbreak. Suriin ang mga pinamumugaran ng lamok ngayong linggo at ihanda ang mga team.",
        "above usual": "Mas mataas sa karaniwan: mas maraming kaso ang inaasahan kaysa karaniwan sa panahong ito. Patuloy na magbantay.",
        "normal": "Normal: walang inaasahang di-pangkaraniwang pagtaas.",
    },
}


# ------------------------------------------------------------------ data

@st.cache_data
def load(panel: str) -> dict:
    d = {name: pd.read_parquet(DATA / f"{panel}_{name}.parquet")
         for name in ("forecast", "drivers", "thresholds", "history", "backtest")}
    d["geo"] = json.loads((DATA / PANELS[panel]["geo"]).read_text())
    return d


@st.cache_data
def load_reports(panel: str) -> dict:
    rep = APP.parent / "reports"
    files = {"backtest": f"backtest_{panel}.csv", "backtest_noweather": f"backtest_{panel}_noweather.csv",
             "alerts": f"alerts_{panel}.csv"}
    return {name: pd.read_csv(rep / f) for name, f in files.items() if (rep / f).exists()}


def fmt(x: float) -> str:
    return f"{x:,.0f}"


def alert_level(q50: pd.Series, q90: pd.Series, alert: pd.Series, epidemic: pd.Series) -> pd.Series:
    lvl = pd.Series(LEVELS[0], index=q50.index)
    lvl[q50 > alert] = LEVELS[1]
    lvl[q90 > epidemic] = LEVELS[2]
    lvl[q50 > epidemic] = LEVELS[3]
    return lvl


@st.cache_data
def replay_origins(panel: str) -> pd.Series:
    """Weeks from which both the 4- and 8-week out-of-sample forecasts exist."""
    b = load(panel)["backtest"]
    b = b.assign(origin=b.target_week - pd.to_timedelta(b.horizon * 7, unit="D"))
    both = b.groupby("origin").horizon.nunique()
    return pd.Series(sorted(both[both == 2].index))


@st.cache_data
def replay_forecast(panel: str, origin: pd.Timestamp) -> pd.DataFrame:
    """Out-of-sample forecasts made at a past week (models trained only on earlier years),
    shaped like the latest-forecast table, plus what actually happened."""
    d = load(panel)
    b = d["backtest"].assign(origin=lambda x: x.target_week - pd.to_timedelta(x.horizon * 7, unit="D"))
    f = b[b.origin == origin].copy()
    static = d["forecast"].drop_duplicates("unit_id")[["unit_id", "unit_name", "population"]]
    f = f.merge(static, on="unit_id").rename(columns={"origin": "week"})
    f["woy"] = f.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
    # Thresholds from years before the forecast, as the backtest used.
    hist = d["history"][d["history"].week < f"{origin.year}-01-01"]
    thr = _thresholds(hist)
    f = f.merge(thr, on=["unit_id", "woy"], how="left")
    f["level"] = alert_level(f.q50, f.q90, f.alert, f.epidemic)
    f["actual_level"] = alert_level(f.actual, f.actual, f.alert, f.epidemic)
    f["q50_per100k"] = f.q50 / f.population * 1e5
    return f


def _thresholds(history: pd.DataFrame) -> pd.DataFrame:
    from alerts import thresholds
    return thresholds(history)


# ------------------------------------------------------------------ sidebar

with st.sidebar:
    lang = st.radio("Language / Wika", ["en", "fil"], format_func=lambda x: "English" if x == "en" else "Filipino",
                    horizontal=True)
    t = T[lang]
    panel = st.selectbox(t["dataset"], list(PANELS), format_func=lambda p: PANELS[p]["label"][lang])
    D = load(panel)
    mode = st.radio(t["mode"], ["latest", "replay"], format_func=lambda m: t[f"mode_{m}"])
    if mode == "replay":
        origins = replay_origins(panel)
        default = origins[origins.dt.month.eq(6)].iloc[0] if origins.dt.month.eq(6).any() else origins.iloc[0]
        origin = st.select_slider(t["origin"], options=list(origins), value=default,
                                  format_func=lambda d: d.strftime("%d %b %Y"))
        horizon = st.select_slider(t["horizon"], options=[4, 8], value=4)
    else:
        horizon = st.select_slider(t["horizon"], options=[2, 4, 6, 8], value=4)
    st.caption("EpiLag-PH · PJDSC 2026")

fc = D["forecast"] if mode == "latest" else replay_forecast(panel, origin)
fc_h = fc[fc.horizon == horizon].copy()
fc_h["level"] = pd.Categorical(fc_h.level, LEVELS, ordered=True)


# ------------------------------------------------------------------ pages

def page_map():
    st.title("EpiLag-PH")
    st.write(t["tagline"])
    origin, target = fc_h.week.max().date(), fc_h.target_week.max().date()
    st.caption(f"{t['as_of']} {origin} · {t['for_week']} {target}")

    if mode == "replay":
        st.info(t["replay_note"])
        crossed = fc_h[fc_h.actual_level == LEVELS[3]]
        flagged = crossed.level.isin(LEVELS[2:]).sum()
        st.markdown(f"**{t['hits']}: {len(crossed)}** · {flagged} {t['caught']}")
    counts = fc_h.level.value_counts()
    cols = st.columns(4)
    for col, lvl, key in zip(cols, reversed(LEVELS), ["warning_n", "watch_n", "above_n", "normal_n"]):
        col.metric(t[key], int(counts.get(lvl, 0)))

    geo_ids = {f["id"] for f in D["geo"]["features"]}
    on_map = fc_h[fc_h.unit_id.isin(geo_ids)]
    hover = on_map[["unit_name", "level"]].astype(str).assign(
        q50=on_map.q50.round(0).astype(int).astype(str), q10=on_map.q10.round(0).astype(int).astype(str),
        q90=on_map.q90.round(0).astype(int).astype(str))
    # Tile-based choropleth: unlike go.Choropleth it does not depend on polygon winding order.
    fig = go.Figure(go.Choroplethmap(
        geojson=D["geo"], locations=on_map.unit_id, z=on_map.level.cat.codes,
        zmin=0, zmax=3, colorscale=[[i / 3, LEVEL_COLOR[l]] for i, l in enumerate(LEVELS)],
        showscale=False, marker_line_color="white", marker_line_width=0.6, marker_opacity=0.9,
        customdata=hover.values,
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]} (%{customdata[3]}–%{customdata[4]})<extra></extra>",
    ))
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=0, b=0),
                      map=dict(style="carto-positron", center=dict(lat=12.3, lon=122.5), zoom=4.4))
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.plotly_chart(fig, width="stretch")
        st.caption("  ·  ".join(f"<span style='color:{LEVEL_COLOR[l]}'>■</span> {l}" for l in LEVELS),
                   unsafe_allow_html=True)
    with right:
        st.subheader(t["rank"])
        table = fc_h.sort_values("q50_per100k", ascending=False)
        view = pd.DataFrame({
            t["area"]: table.unit_name, t["level"]: table.level.astype(str),
            t["cases"]: table.q50.round(0).astype(int),
            t["range"]: table.q10.round(0).astype(int).astype(str) + "–" + table.q90.round(0).astype(int).astype(str),
            t["per100k"]: table.q50_per100k.round(1),
        })
        if mode == "replay":
            view[t["actual_col"]] = table.actual.round(0).astype("Int64").astype(str) + " · " + table.actual_level
        st.dataframe(view, hide_index=True, width="stretch", height=560)


def threshold_series(unit_id: str, weeks: pd.Series) -> pd.Series:
    # In replay, thresholds come only from years before the replayed year (as in the backtest).
    table = _thresholds(D["history"][D["history"].week < f"{origin.year}-01-01"]) if mode == "replay" else D["thresholds"]
    thr = table[table.unit_id == unit_id].set_index("woy").epidemic
    woy = weeks.dt.isocalendar().week.astype(int).clip(upper=52)
    return woy.map(thr).values


def page_unit():
    names = fc_h.sort_values("q50_per100k", ascending=False)
    unit_name = st.selectbox(t["pick"], names.unit_name)
    unit_id = names[names.unit_name == unit_name].unit_id.iloc[0]
    row = fc_h[fc_h.unit_id == unit_id].iloc[0]

    st.subheader(unit_name)
    a, b, c = st.columns(3)
    a.metric(t["level"], row.level)
    b.metric(f"{t['cases']} ({horizon} wk)", fmt(row.q50), help=f"{t['range']}: {fmt(row.q10)}–{fmt(row.q90)}")
    c.metric(t["per100k"], f"{row.q50_per100k:.1f}")
    st.info(ALERT_TEXT[lang][row.level])

    hist = D["history"][D["history"].unit_id == unit_id]
    if mode == "replay":
        hist = hist[(hist.week >= origin - pd.Timedelta(weeks=104)) & (hist.week <= origin + pd.Timedelta(weeks=26))]
    else:
        hist = hist[hist.week >= hist.week.max() - pd.Timedelta(weeks=156)]
    bt = D["backtest"][(D["backtest"].unit_id == unit_id) & (D["backtest"].horizon == 4)].sort_values("target_week")
    bt = bt[bt.target_week.between(hist.week.min(), hist.week.max())]
    now = fc[fc.unit_id == unit_id].sort_values("target_week")

    fig = go.Figure()
    if not bt.empty:
        for year, g in bt.groupby("test_year"):
            fig.add_trace(go.Scatter(x=pd.concat([g.target_week, g.target_week[::-1]]),
                                     y=pd.concat([g.q90, g.q10[::-1]]), fill="toself", fillcolor=BAND,
                                     line=dict(width=0), hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(x=g.target_week, y=g.q50, line=dict(color=ACCENT, width=1.5, dash="dot"),
                                     name=t["fc4"], showlegend=bool(year == bt.test_year.min())))
    fig.add_trace(go.Scatter(x=hist.week, y=hist.cases, line=dict(color="#1F2933", width=1.6), name=t["actual"]))
    fig.add_trace(go.Scatter(x=hist.week, y=threshold_series(unit_id, hist.week),
                             line=dict(color=LEVEL_COLOR["outbreak warning"], width=1, dash="dash"), name=t["epi_line"]))
    fig.add_trace(go.Scatter(x=now.target_week, y=now.q50, mode="lines+markers",
                             error_y=dict(type="data", symmetric=False, array=now.q90 - now.q50,
                                          arrayminus=now.q50 - now.q10, color=ACCENT),
                             line=dict(color=ACCENT, width=2.5),
                             name=t["fcnow"] if mode == "latest" else f"{t['fcnow']} ({origin:%d %b %Y})"))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=30, b=0), title=t["history"],
                      legend=dict(orientation="h", y=-0.15), plot_bgcolor="white",
                      yaxis=dict(gridcolor="#E4E7EB", title=t["cases"]))
    st.plotly_chart(fig, width="stretch")

    if mode == "replay":
        return
    st.subheader(t["why"])
    dr = D["drivers"][(D["drivers"].unit_id == unit_id) & (D["drivers"].horizon == horizon)]
    dr = dr.reindex(dr.shap.abs().sort_values(ascending=False).index).head(10)[::-1]
    bar = go.Figure(go.Bar(x=dr.shap, y=dr.driver, orientation="h",
                           marker_color=[ACCENT if v > 0 else MUTED for v in dr.shap]))
    bar.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white",
                      xaxis=dict(gridcolor="#E4E7EB", zeroline=True, zerolinecolor="#9AA5B1"))
    st.plotly_chart(bar, width="stretch")
    st.caption(t["why_note"])


def page_proof():
    st.header(t["nav_proof"])
    rep = load_reports(panel)
    if "backtest" not in rep:
        st.warning("No backtest results for this dataset yet.")
        return
    bt = rep["backtest"]
    st.markdown("Each test year was forecast **only from earlier years** (no peeking). "
                "Lower error is better. Baselines: *same week last year* and *same as this week*.")
    view = bt[["test_year", "horizon", "mae_epilag", "mae_seasonal_naive", "mae_persistence", "coverage_10_90"]].copy()
    view.columns = ["Test year", "Weeks ahead", "EpiLag error", "Same week last year", "Same as this week",
                    "Range coverage (target 80%)"]
    st.dataframe(view.style.format({"EpiLag error": "{:.0f}", "Same week last year": "{:.0f}",
                                    "Same as this week": "{:.0f}", "Range coverage (target 80%)": "{:.0%}"}),
                 hide_index=True, width="stretch")

    if "alerts" in rep:
        st.subheader("Early warning")
        al = rep["alerts"]
        al = al[al.horizon == horizon]
        st.markdown(f"Outbreak starts warned **{horizon} weeks ahead** "
                    "(*watch* = upper end of the range above the epidemic threshold; "
                    "*warning* = middle forecast above it).")
        piv = al.pivot_table(index="test_year", columns="rule", values=["share_warned", "false_alarm_share"])
        piv.columns = [f"{'Caught' if a == 'share_warned' else 'False alarms'} ({'watch' if r == 'warn_upper' else 'warning'})"
                       for a, r in piv.columns]
        st.dataframe(piv.style.format("{:.0%}"), width="stretch")

    if "backtest_noweather" in rep:
        st.subheader("Does weather help?")
        nw = rep["backtest_noweather"].set_index(["test_year", "horizon"]).mae_epilag
        w = bt.set_index(["test_year", "horizon"]).mae_epilag
        gain = (1 - w / nw).rename("Error reduction from weather").reset_index()
        st.dataframe(gain.style.format({"Error reduction from weather": "{:+.0%}"}), hide_index=True,
                     width="stretch")
        st.caption("Honest result: most of the skill comes from recent cases and season. "
                   "Weather adds a modest gain at 4-8 weeks in some years and none in others.")


def page_budget():
    st.header(t["nav_budget"])
    st.caption("Ranks where each peso prevents the most forecast cases over the next 8 weeks. "
               "Costs are example values: replace them with your LGU's own costs.")
    budget = st.number_input(t["budget"], min_value=0, value=5_000_000, step=500_000)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Clean-up drive + container covers**")
        cost_a = st.number_input(t["cost"], value=15.0, step=1.0, key="ca")
        eff_a = st.slider(t["effect"], 0.0, 0.8, (0.10, 0.50), key="ea")
    with c2:
        st.markdown("**Targeted fogging**")
        cost_b = st.number_input(t["cost"], value=25.0, step=1.0, key="cb")
        eff_b = st.slider(t["effect"], 0.0, 0.8, (0.0, 0.10), key="eb")
    actions = (
        Action("Clean-up drive + container covers", cost_a, eff_a[0], sum(eff_a) / 2, eff_a[1], 0.30),
        Action("Targeted fogging", cost_b, eff_b[0], sum(eff_b) / 2, eff_b[1], 0.10),
    )
    plan = allocate(fc[fc.horizon.isin([2, 4, 6, 8])], budget, actions)
    if plan.empty:
        st.info("No funded actions. Increase the budget.")
        return
    lo, mid, hi = plan.averted_low.sum(), plan.averted_mid.sum(), plan.averted_high.sum()
    m1, m2 = st.columns(2)
    m1.metric(t["averted"], f"{fmt(lo)} / {fmt(mid)} / {fmt(hi)}")
    m2.metric("Pesos per case averted (central)", fmt(plan.spend.sum() / mid) if mid else "–")
    st.subheader(t["plan"])
    st.dataframe(pd.DataFrame({
        t["area"]: plan.unit_name, "Action": plan.action, "Spend (PHP)": plan.spend.map(fmt),
        "People covered": plan.people_covered.map(fmt),
        "Cases averted (low–high)": plan.averted_low.round(0).astype(int).astype(str) + "–"
        + plan.averted_high.round(0).astype(int).astype(str),
    }), hide_index=True, width="stretch")
    st.caption("Effect ranges are cautious, from Bowman et al. (2016): community clean-up with container covers "
               "cut dengue risk in a few small trials (OR 0.22); fogging showed little effect on cases.")


def page_qc():
    st.header(t["qc_head"])
    st.caption(t["qc_note"])
    if panel != "region_qc":
        st.info("Switch the data to 'Regions + Quezon City' in the sidebar.")
        return
    brgy = pd.read_csv(DATA / "qc_barangays.csv")
    qc = fc[(fc.unit_id == "QC")].sort_values("horizon")
    qc8 = qc.q50.mean() * 8
    brgy["expected_8wk"] = brgy.share * qc8
    lvl = qc[qc.horizon == horizon].level.iloc[0]
    a, b = st.columns(2)
    a.metric(t["level"], lvl)
    b.metric("City-wide forecast, next 8 weeks", fmt(qc8))
    st.info(ALERT_TEXT[lang][lvl])
    top = brgy.head(20)[::-1]
    fig = go.Figure(go.Bar(x=top.expected_8wk, y=top.Barangay, orientation="h", marker_color=ACCENT))
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white",
                      xaxis=dict(title="Expected cases, next 8 weeks", gridcolor="#E4E7EB"))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(brgy.rename(columns={"cases_2022_2025": "Cases 2022-2025", "cases_2025": "Cases 2025",
                                      "share": "Share of city", "expected_8wk": "Expected, next 8 weeks"}),
                 hide_index=True, width="stretch")


def page_about():
    st.header(t["nav_about"])
    st.markdown("""
**What EpiLag-PH does.** It forecasts weekly dengue cases 2-8 weeks ahead for each area, from recent cases,
season, and rain, heat and humidity in the past 12 weeks. It flags areas likely to pass the epidemic threshold,
explains each forecast, and ranks where a limited budget prevents the most cases.

**Method.** LightGBM quantile models (10th, 50th, 90th percentile), one per horizon. Ranges are calibrated with
conformalized quantile regression. Thresholds per area and week of year from earlier years only:
usual = mean, epidemic = mean + 2 SD. Explanations with SHAP.

**Data.**
- DOH Epidemiology Bureau dengue cases and deaths, 2016-2021, via HDX (PJDSC official catalogue).
- UPRI-NOAH weekly dengue and rainfall: 17 regions (2016-2019, 2022-2025) and Quezon City (2010-2025), Zenodo 19448695, ODC-ODbL.
- Weather: ERA5 reanalysis via the Open-Meteo archive API, at each area's centroid.
- Population: OCHA COD-PS (PSA-based), 2022. Codes and boundaries: OCHA COD-AB; maps: faeldon/philippines-json-maps (MIT).

**Limits (read before use).**
- Province data ends in January 2021; the province view is a historical replay.
- Reported cases undercount true infections (about 4.7 times in one Cebu City study).
- One weather point per area: large provinces are simplified.
- Weather adds only a modest gain over recent cases and season.
- The 'watch' level catches most outbreak starts but has many false alarms; the 'warning' level is stricter.
- Budget effects and costs are assumptions, shown as ranges and editable.
- Barangay ranking in Quezon City uses yearly shares, not weekly barangay forecasts.
""")


pages = {
    t["nav_map"]: page_map, t["nav_unit"]: page_unit, t["nav_proof"]: page_proof,
    t["nav_budget"]: page_budget, t["nav_qc"]: page_qc, t["nav_about"]: page_about,
}
start = st.query_params.get("page")  # optional deep link, e.g. ?page=budget
nav = st.navigation([st.Page(fn, title=title, url_path=fn.__name__.removeprefix("page_"),
                             default=(fn.__name__ == f"page_{start}") if start else (fn is page_map))
                     for title, fn in pages.items()])
nav.run()
