"""Smoke test: every page renders without errors, for both datasets and both languages."""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")
PAGES = ["home", "map", "unit", "proof", "budget", "public", "qc", "about"]


@pytest.mark.parametrize("mode", ["latest", "replay"])
@pytest.mark.parametrize("panel", ["region_qc", "province"])
@pytest.mark.parametrize("lang", ["en", "fil"])
@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page, lang, panel, mode):
    at = AppTest.from_file(APP, default_timeout=90)
    at.query_params["page"] = page  # read by the app to pick the start page
    at.run()
    at.radio(key="lang").set_value(lang).run()
    at.radio(key="panel").set_value(panel).run()
    at.radio(key="mode").set_value(mode).run()
    assert not at.exception, [e.message for e in at.exception]


def test_replay_june_2019_flags_most_outbreaks():
    """The demo claim: forecasts made 2 Jun 2019 flagged most areas that later crossed the threshold."""
    at = AppTest.from_file(APP, default_timeout=90)
    at.query_params["page"] = "map"
    at.run()
    at.radio(key="mode").set_value("replay").run()
    m = next(re.search(r'data-crossed="(\d+)" data-flagged="(\d+)"', e.value) for e in at.markdown if "data-crossed" in e.value)
    crossed, flagged = int(m.group(1)), int(m.group(2))
    assert crossed > 0 and flagged / crossed >= 0.8


def test_story_button_switches_to_province_replay():
    at = AppTest.from_file(APP, default_timeout=90)
    at.query_params["page"] = "home"
    at.run()
    at.button(key="story_btn").click().run()
    assert at.radio(key="panel").value == "province" and at.radio(key="mode").value == "replay"
    assert not at.exception
