"""Publish the latest forecasts as open data in docs/data/ (CSV and JSON), for researchers, newsrooms and other apps.

  epilag_forecast_{panel}.csv|json     latest forecasts, with the alert track record of each area at that horizon
  epilag_reliability_{panel}.csv|json  alert track record per area and horizon (src/reliability.py)
  alerts.xml                           RSS feed: areas on watch or outbreak warning in the latest forecast
  alerts.ics                           calendar feed: one all-day event per area and forecast week on watch or warning

The feeds cover the regions and Quezon City (data to the latest week); the province data ends in January 2021.
Usage: python scripts/export_open_data.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlencode
from xml.sax.saxutils import escape

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from reliability import track_record  # noqa: E402

OUT = ROOT / "docs" / "data"
DATA = ROOT / "app" / "data"
SITE = "https://romeo-04.github.io/epilag/"
COLUMNS = {
    "unit_id": "area_code", "unit_name": "area_name", "week": "forecast_made_week_ending", "horizon": "weeks_ahead",
    "target_week": "target_week_ending", "q10": "cases_low", "q50": "cases_middle", "q90": "cases_high",
    "q50_per100k": "cases_middle_per_100k", "alert": "usual_level", "epidemic": "epidemic_threshold", "level": "alert_level",
    "population": "population",
}
RELIABILITY = {"alert_weeks": "alert_weeks", "alert_weeks_right": "alert_weeks_right", "reliability": "alert_reliability",
               "grade": "reliability_grade", "onsets": "outbreak_starts", "onsets_caught": "outbreak_starts_caught",
               "years": "test_years"}
ALERTS = ("watch", "outbreak warning")
LEVEL_TITLE = {"watch": "Dengue watch", "outbreak warning": "Dengue outbreak warning"}


def record_horizon(h: int) -> int:
    """The backtest horizon a track record uses (site/src/app/data.js recordHorizon): 8 for 6-8 weeks, else 4."""
    return 8 if h >= 6 else 4


def reliability(panel: str) -> pd.DataFrame:
    hist = pd.read_parquet(DATA / f"{panel}_history.parquet")[["unit_id", "week", "cases"]]
    back = pd.read_parquet(DATA / f"{panel}_backtest.parquet")
    out = [track_record(hist, back, h).assign(backtest_weeks_ahead=h) for h in sorted(back.horizon.unique())]
    return pd.concat(out, ignore_index=True)


def app_link(area: str, page: str = "unit") -> str:
    return f"{SITE}web/?{urlencode({'page': page, 'panel': 'region_qc', 'mode': 'latest', 'h': 4, 'lang': 'en', 'area': area})}"


def rss(f: pd.DataFrame, made: str) -> str:
    """Areas on watch or warning at 4 weeks ahead; a new item per area each forecast week."""
    now = format_datetime(datetime.now(timezone.utc))
    alerts = f[(f.weeks_ahead == 4) & f.alert_level.isin(ALERTS)].sort_values(["alert_level", "area_name"], ascending=[False, True])
    items = []
    for r in alerts.itertuples():
        right = "" if pd.isna(r.alert_reliability) else f" In past tests, {round(r.alert_reliability * 100)}% of this area's alert weeks were right."
        desc = (f"{r.area_name}: {r.alert_level} for the week ending {r.target_week_ending}. Forecast {r.cases_middle:,.0f} cases "
                f"(likely {r.cases_low:,.0f}–{r.cases_high:,.0f}); epidemic line {r.epidemic_threshold:,.0f}.{right}")
        items.append((f"{LEVEL_TITLE[r.alert_level]}: {r.area_name}, week ending {r.target_week_ending}", app_link(r.area_code),
                      desc, f"epilag-{r.area_code}-{made}"))
    if not items:
        items.append((f"No area on watch or warning (forecast of {made})", f"{SITE}web/",
                      "No region or Quezon City is on watch or outbreak warning 4 weeks ahead.", f"epilag-quiet-{made}"))
    body = "".join(f"<item><title>{escape(t)}</title><link>{escape(link)}</link><description>{escape(d)}</description>"
                   f'<guid isPermaLink="false">{escape(g)}</guid><pubDate>{now}</pubDate></item>\n' for t, link, d, g in items)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n'
            "<title>EpiLag-PH dengue alerts</title>\n"
            f"<link>{SITE}web/</link>\n"
            f'<atom:link href="{SITE}data/alerts.xml" rel="self" type="application/rss+xml"/>\n'
            f"<description>Philippine regions and Quezon City on dengue watch or outbreak warning, 4 weeks ahead. Forecast made from data to {made}.</description>\n"
            f"<language>en</language><lastBuildDate>{now}</lastBuildDate>\n{body}</channel></rss>\n")


def _fold(line: str) -> str:
    """RFC 5545: lines of at most 75 octets, continued with a leading space."""
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 75:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    return "\r\n".join(out + [cur])


def _ics_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics(f: pd.DataFrame, made: str) -> str:
    """One all-day event per area and forecast week on watch or warning (the week Monday-Sunday it ends)."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//EpiLag-PH//Dengue alerts//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:EpiLag-PH dengue alerts", "X-WR-CALDESC:Regions and Quezon City on dengue watch or outbreak warning",
             "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]
    for r in f[f.alert_level.isin(ALERTS)].sort_values(["target_week_ending", "area_name"]).itertuples():
        end = datetime.strptime(r.target_week_ending, "%Y-%m-%d")
        start = end - timedelta(days=6)
        right = "" if pd.isna(r.alert_reliability) else f" Past alert weeks right: {round(r.alert_reliability * 100)}%."
        desc = (f"{r.area_name}: {r.alert_level}, forecast made {r.weeks_ahead} weeks ahead from data to {made}. "
                f"Forecast {r.cases_middle:,.0f} cases (likely {r.cases_low:,.0f}-{r.cases_high:,.0f}); epidemic line "
                f"{r.epidemic_threshold:,.0f}.{right} What to do: {app_link(r.area_code)}")
        lines += ["BEGIN:VEVENT", f"UID:{r.area_code}-{r.target_week_ending}-h{r.weeks_ahead}@epilag-ph", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{start:%Y%m%d}", f"DTEND;VALUE=DATE:{end + timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{_ics_text(f'{LEVEL_TITLE[r.alert_level]}: {r.area_name} ({r.weeks_ahead} wk ahead)')}",
                  f"DESCRIPTION:{_ics_text(desc)}", f"URL:{app_link(r.area_code)}", "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"source": "EpiLag-PH, https://github.com/Romeo-04/epilag", "files": {}}
    for panel, label in [("region_qc", "17 regions and Quezon City"), ("province", "86 provinces (data ends Jan 2021)")]:
        rel = reliability(panel)
        f = pd.read_parquet(DATA / f"{panel}_forecast.parquet")[list(COLUMNS)].rename(columns=COLUMNS)
        for col in ("forecast_made_week_ending", "target_week_ending"):
            f[col] = f[col].dt.strftime("%Y-%m-%d")
        for col in ("cases_low", "cases_middle", "cases_high", "usual_level", "epidemic_threshold"):
            f[col] = f[col].round(1)
        f["cases_middle_per_100k"] = f["cases_middle_per_100k"].round(2)
        f["backtest_weeks_ahead"] = f.weeks_ahead.map(record_horizon)
        f = f.merge(rel[["unit_id", "backtest_weeks_ahead", "reliability", "grade"]]
                    .rename(columns={"unit_id": "area_code", "reliability": "alert_reliability", "grade": "reliability_grade"}),
                    on=["area_code", "backtest_weeks_ahead"], how="left").drop(columns="backtest_weeks_ahead")
        f["alert_reliability"] = f["alert_reliability"].round(3)
        f = f.sort_values(["weeks_ahead", "area_name"])
        name = f"epilag_forecast_{panel}"
        f.to_csv(OUT / f"{name}.csv", index=False)
        (OUT / f"{name}.json").write_text(json.dumps(f.to_dict("records"), indent=1))
        meta["files"][name] = {"covers": label, "rows": len(f), "forecast_made_week_ending": f.forecast_made_week_ending.max()}
        print(name, len(f), "rows")

        names = f.drop_duplicates("area_code").set_index("area_code").area_name
        r = rel.rename(columns={"unit_id": "area_code", **RELIABILITY})
        r.insert(1, "area_name", r.area_code.map(names))
        r["alert_reliability"] = r["alert_reliability"].round(3)
        r = r[["area_code", "area_name", "backtest_weeks_ahead", *RELIABILITY.values()]].sort_values(["backtest_weeks_ahead", "area_name"])
        rname = f"epilag_reliability_{panel}"
        r.to_csv(OUT / f"{rname}.csv", index=False)
        (OUT / f"{rname}.json").write_text(json.dumps(r.to_dict("records"), indent=1))
        meta["files"][rname] = {"covers": label, "rows": len(r)}
        print(rname, len(r), "rows")

        if panel == "region_qc":
            made = f.forecast_made_week_ending.max()
            (OUT / "alerts.xml").write_text(rss(f, made), encoding="utf-8")
            (OUT / "alerts.ics").write_bytes(ics(f, made).encode("utf-8"))
            meta["files"]["alerts.xml"] = {"covers": f"{label}: watch and outbreak warning, 4 weeks ahead", "format": "RSS 2.0"}
            meta["files"]["alerts.ics"] = {"covers": f"{label}: watch and outbreak warning, 2-8 weeks ahead", "format": "iCalendar"}
            print("alerts.xml, alerts.ics")
    (OUT / "index.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
