"""Play Dengue Drill on the live site and capture in-game moments for the deck."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "assets"


def skip_tips(pg):
    for name in ("Skip", "Got it", "Close"):
        loc = pg.get_by_text(name, exact=True)
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            pg.wait_for_timeout(400)


def play_round(pg, shots_at=None, prefix=""):
    skip_tips(pg)
    for turn in range(8):
        skip_tips(pg)
        rows = pg.locator("#plist .prow")
        for k in range(min(2, rows.count())):
            rows.nth(k).click()
            pg.wait_for_timeout(250)
            dep = pg.get_by_role("button", name=__import__("re").compile("Send team|Deploy team"))
            if dep.count() and dep.first.is_enabled():
                dep.first.click()
                pg.wait_for_timeout(300)
        if shots_at is not None and turn == shots_at:
            pg.wait_for_timeout(1200)
            pg.screenshot(path=str(OUT / f"{prefix}board.png"))
        end = pg.locator("#end")
        if not end.count() or not end.is_visible():
            break
        end.click()
        pg.wait_for_timeout(900)
        if "unused" in (end.inner_text() if end.count() and end.is_visible() else ""):
            end.click()
        pg.wait_for_timeout(1400)
        if pg.locator("#s-report").is_visible():
            break


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1.5)
    pg.goto("https://epilag.vercel.app/drill/", wait_until="networkidle")
    pg.wait_for_timeout(3000)
    pg.click("#start")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / "drill_brief.png"))
    pg.click("#go-r1")
    pg.wait_for_timeout(2500)
    play_round(pg, shots_at=2, prefix="drill_r1_")
    pg.wait_for_timeout(2000)
    pg.screenshot(path=str(OUT / "drill_report_r1.png"))
    pg.wait_for_selector("#next-r", timeout=60000)
    pg.click("#next-r")
    pg.wait_for_timeout(2500)
    if pg.locator("#go-r2").is_visible():  # the forecaster chooser between the rounds
        pg.click("#go-r2")
        pg.wait_for_timeout(2500)
    play_round(pg, shots_at=1, prefix="drill_r2_")
    pg.wait_for_timeout(2000)
    pg.screenshot(path=str(OUT / "drill_report_r2.png"))
    nxt = pg.locator("#next-r")
    if nxt.count():
        nxt.click()
        pg.wait_for_timeout(3000)
        pg.screenshot(path=str(OUT / "drill_vs.png"))
    b.close()
print("done")
