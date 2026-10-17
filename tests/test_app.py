"""Smoke test: every page renders without errors, for both datasets and both languages."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")
PAGES = ["map", "unit", "proof", "budget", "qc", "about"]


@pytest.mark.parametrize("mode", ["latest", "replay"])
@pytest.mark.parametrize("panel", [0, 1])
@pytest.mark.parametrize("lang", ["en", "fil"])
@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page, lang, panel, mode):
    at = AppTest.from_file(APP, default_timeout=90)
    at.query_params["page"] = page  # read by the app to pick the start page
    at.run()
    at.sidebar.radio[0].set_value(lang).run()
    at.sidebar.selectbox[0].set_value(at.sidebar.selectbox[0].options[panel]).run()
    at.sidebar.radio[1].set_value(mode).run()
    assert not at.exception, [e.message for e in at.exception]


def test_replay_june_2019_flags_most_outbreaks():
    """The demo claim: forecasts made 2 Jun 2019 flagged most areas that later crossed the threshold."""
    at = AppTest.from_file(APP, default_timeout=90)
    at.query_params["page"] = "map"
    at.run()
    at.sidebar.radio[1].set_value("replay").run()
    line = next(m.value for m in at.markdown if "crossed" in m.value)
    crossed, flagged = [int(s) for s in line.replace("*", "").split() if s.isdigit()][:2]
    assert crossed > 0 and flagged / crossed >= 0.8
