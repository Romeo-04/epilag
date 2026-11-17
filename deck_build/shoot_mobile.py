"""Phone-size screenshot of the residents' page for the deck."""
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path(__file__).parent / "assets"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.goto("https://epilag.vercel.app/web/?panel=region_qc&mode=replay&h=4&lang=fil&origin=2024-09-15&page=public&region=R_NCR&area=QC", wait_until="networkidle")
    pg.wait_for_timeout(2000)
    for name in ("Laktawan", "Skip"):
        loc = pg.get_by_role("button", name=name)
        if loc.count() and loc.first.is_visible():
            loc.first.click(); pg.wait_for_timeout(500)
    pg.wait_for_timeout(1000)
    box = pg.get_by_text("Maaaring tumaas", exact=False).first.bounding_box()
    y = box["y"] + pg.evaluate("window.scrollY") - 130
    pg.screenshot(path=str(OUT / "phone_public_fil.png"), full_page=True, clip={"x": 0, "y": y, "width": 390, "height": 844})
    b.close()
print("done")
