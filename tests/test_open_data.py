"""Open data and alert feeds (scripts/export_open_data.py): the track record columns, the RSS feed and the calendar.

The latest regional forecast may have no area on alert (a quiet season), so the feeds are also built from the 2021
province forecast, which has areas on watch."""
import sys
import xml.dom.minidom
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import export_open_data as e  # noqa: E402
from reliability import grade, track_record  # noqa: E402

OUT = ROOT / "docs" / "data"
pytestmark = pytest.mark.skipif(not (OUT / "epilag_reliability_region_qc.csv").exists(), reason="run scripts/export_open_data.py first")


def _forecast(panel):
    return pd.read_csv(OUT / f"epilag_forecast_{panel}.csv", dtype={"target_week_ending": str, "forecast_made_week_ending": str})


@pytest.mark.parametrize("panel", ["region_qc", "province"])
def test_forecast_reliability_matches_track_record(panel):
    f = _forecast(panel)
    hist = pd.read_parquet(ROOT / "app" / "data" / f"{panel}_history.parquet")
    back = pd.read_parquet(ROOT / "app" / "data" / f"{panel}_backtest.parquet")
    for h in (2, 4, 6, 8):
        t = track_record(hist, back, e.record_horizon(h)).set_index("unit_id")
        fh = f[f.weeks_ahead == h].set_index("area_code")
        assert (fh.reliability_grade == t.grade.reindex(fh.index)).all()
        assert fh.alert_reliability.values == pytest.approx(t.reliability.reindex(fh.index).round(3).values, nan_ok=True)


def test_grades():
    assert grade(3, 3) == "too few"
    assert [grade(10, k) for k in (6, 5, 4, 3)] == ["high", "medium", "medium", "low"]


@pytest.mark.parametrize("panel", ["region_qc", "province"])
def test_rss_is_valid(panel):
    f = _forecast(panel)
    doc = xml.dom.minidom.parseString(e.rss(f, f.forecast_made_week_ending.max()))
    items = doc.getElementsByTagName("item")
    n_alert = int(((f.weeks_ahead == 4) & f.alert_level.isin(e.ALERTS)).sum())
    assert len(items) == max(n_alert, 1)
    guids = [i.getElementsByTagName("guid")[0].firstChild.data for i in items]
    assert len(set(guids)) == len(guids)


@pytest.mark.parametrize("panel", ["region_qc", "province"])
def test_calendar_is_valid(panel):
    f = _forecast(panel)
    s = e.ics(f, f.forecast_made_week_ending.max())
    assert s.startswith("BEGIN:VCALENDAR\r\n") and s.endswith("END:VCALENDAR\r\n")
    lines = s.split("\r\n")[:-1]
    assert all(len(line.encode("utf-8")) <= 75 for line in lines)
    assert "\n" not in s.replace("\r\n", "")
    n = int(f.alert_level.isin(e.ALERTS).sum())
    assert s.count("BEGIN:VEVENT") == s.count("END:VEVENT") == n
    if panel == "province":
        assert n > 0
    uids = [line for line in lines if line.startswith("UID:")]
    assert len(set(uids)) == len(uids)
