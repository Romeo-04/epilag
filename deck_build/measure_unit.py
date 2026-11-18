"""Bounding boxes (as % of the screenshot) of the parts of the area page we label on slide 16."""
import json

from playwright.sync_api import sync_playwright

URL = "https://epilag.vercel.app/web/?panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15&page=unit&region=R_NCR&area=QC"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(2500)
    for name in ("Skip", "Close"):
        loc = pg.get_by_role("button", name=name)
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            pg.wait_for_timeout(500)
    out = {}
    for key, text in [("watch", "Watch"), ("cases", "Forecast cases"), ("todo", "What to do now"), ("chart", "Weekly cases, forecasts")]:
        loc = pg.get_by_text(text, exact=False)
        for k in range(loc.count()):
            bb = loc.nth(k).bounding_box()
            if bb and bb["y"] < 900 and bb["x"] > 150:
                out[key] = {"x": round(bb["x"] / 14.4, 1), "y": round(bb["y"] / 9, 1)}
                break
    pg.screenshot(path="deck_build/assets/app_unit.png")
    print(json.dumps(out))
    b.close()
