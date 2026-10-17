"""Capture app screenshots for the deck. Needs the app running on localhost:8599 and Chrome installed.
Usage: python scripts/screenshots.py"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
SHOTS = [("map_latest", "map", False), ("map_replay_2019", "map", True), ("unit_replay_2019", "unit", True),
         ("proof", "proof", False), ("budget_replay_2019", "budget", True), ("qc", "qc", False)]

OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 960})
    for name, path, replay in SHOTS:
        page.goto("http://localhost:8599/" + ("" if path == "map" else path))
        page.wait_for_selector("[data-testid='stSidebar']", timeout=60000)
        page.wait_for_timeout(3000)
        if replay:
            page.get_by_text("Replay a past week").click()
        page.wait_for_timeout(7000)
        page.screenshot(path=OUT / f"{name}.png")
        print("saved", name)
    browser.close()
