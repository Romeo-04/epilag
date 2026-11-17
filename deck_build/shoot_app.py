"""Fresh screenshots of the live app for the deck (slides 16-17)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)
BASE = "https://epilag.vercel.app/web/?panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15"
PAGES = {
    "app_home": "&page=home",
    "app_map": "&page=map",
    "app_unit": "&page=unit&region=R_NCR&area=QC",
    "app_budget": "&page=budget",
    "app_public": "&page=public&region=R_NCR&area=QC",
}

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    # first visit: the onboarding guide opens on its own
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
    pg = ctx.new_page()
    pg.goto(BASE + "&page=home", wait_until="networkidle")
    pg.wait_for_timeout(2500)
    pg.screenshot(path=str(OUT / "app_onboarding.png"))
    # close the guide, then the other pages
    for label in ("Skip", "Close"):
        btn = pg.get_by_role("button", name=label)
        if btn.count():
            btn.first.click()
            break
    for name, q in PAGES.items():
        pg.goto(BASE + q, wait_until="networkidle")
        pg.wait_for_timeout(2500)
        pg.screenshot(path=str(OUT / f"{name}.png"))
    pg.goto("https://epilag.vercel.app/drill/", wait_until="networkidle")
    pg.wait_for_timeout(4000)
    pg.screenshot(path=str(OUT / "drill_title.png"))
    b.close()
print("done")
