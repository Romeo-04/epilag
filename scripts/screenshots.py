"""Capture app screenshots for the deck and README. Needs the app running on localhost:8599 and Chrome.
Usage: python scripts/screenshots.py [name ...]"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
# name, page, replay (2 Jun 2019), provinces, full page
SHOTS = [("home", "home", False, False, True), ("home_replay_2019", "home", True, True, False),
         ("map_latest", "map", False, False, False), ("map_replay_2019", "map", True, True, True),
         ("unit_replay_2019", "unit", True, True, True), ("unit_latest", "unit", False, False, True),
         ("proof", "proof", False, False, True), ("budget_replay_2019", "budget", True, True, True),
         ("qc", "qc", False, False, True), ("public", "public", True, True, True)]


def open_app(page, path, replay, provinces):
    page.goto(f"http://localhost:8599/?page={path}")
    page.wait_for_selector(".st-key-topbar", timeout=90000)
    page.wait_for_timeout(2500)
    if provinces:
        page.locator(".st-key-panel").get_by_text("Provinces").click()
        page.wait_for_timeout(2500)
    if replay:
        page.locator(".st-key-mode").get_by_text("Replay a past week").click()
    page.wait_for_timeout(7000)


if __name__ == "__main__":
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        for name, path, replay, provinces, full in SHOTS:
            if only and name not in only:
                continue
            open_app(page, path, replay, provinces)
            if full:  # Streamlit scrolls inside its own container, so grow the viewport to the content height
                height = page.evaluate("document.querySelector('[data-testid=stMain]').scrollHeight")
                page.set_viewport_size({"width": 1440, "height": min(height, 4000)})
                page.wait_for_timeout(2500)
            page.screenshot(path=OUT / f"{name}.png")
            page.set_viewport_size({"width": 1440, "height": 960})
            print("saved", name)
        browser.close()
