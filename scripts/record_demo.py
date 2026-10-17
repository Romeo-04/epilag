"""Record a silent, captioned walkthrough of the app that follows docs/video_script.md.
Needs the app on localhost:8599, Chrome, and Playwright's ffmpeg (`python -m playwright install ffmpeg`).
Writes docs/demo.webm (about 2.5 minutes; needs ~30 MB free). Add the voice-over in any video editor.

Usage: python scripts/record_demo.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs"
URL = "http://localhost:8599/"
SIZE = {"width": 1920, "height": 1080}

CAPTION_JS = """text => {
  let el = document.getElementById('demo-caption');
  if (!el) {
    el = document.createElement('div'); el.id = 'demo-caption';
    Object.assign(el.style, {position: 'fixed', left: '50%', bottom: '32px', transform: 'translateX(-50%)',
      background: 'rgba(31,41,51,.92)', color: '#fff', padding: '14px 24px', borderRadius: '12px',
      font: '600 22px Segoe UI, sans-serif', zIndex: 99999, maxWidth: '1400px', textAlign: 'center'});
    document.body.appendChild(el);
  }
  el.textContent = text;
}"""


def caption(page, text, seconds):
    page.evaluate(CAPTION_JS, text)
    page.wait_for_timeout(int(seconds * 1000))


def open_page(page, path, replay):
    page.goto(URL + path)
    page.wait_for_selector("[data-testid='stSidebar']", timeout=60000)
    page.wait_for_timeout(2500)
    if replay:
        page.get_by_text("Replay a past week").click()
        page.wait_for_timeout(4000)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport=SIZE, record_video_dir=str(OUT), record_video_size=SIZE)
    page = ctx.new_page()

    open_page(page, "", replay=False)
    caption(page, "EpiLag-PH: dengue early warning for Philippine LGUs", 6)
    caption(page, "Forecast, flag, plan: cases 2-8 weeks ahead for every province, region and Quezon City", 8)

    open_page(page, "", replay=True)
    caption(page, "Replay: what EpiLag-PH would have said on 2 June 2019 (models trained only on earlier years)", 9)
    caption(page, "Red = outbreak warning, orange = watch. Regions: 11 of 11 that crossed the threshold were flagged", 9)
    page.get_by_test_id("stSidebar").get_by_role("combobox").first.click()
    page.get_by_text("Provinces (historical replay").click()
    page.wait_for_timeout(2500)
    page.get_by_text("Replay a past week").click()
    page.wait_for_timeout(3500)
    caption(page, "Provinces: 4 weeks later 32 crossed the epidemic threshold. 30 were already flagged.", 11)

    open_page(page, "unit", replay=True)
    caption(page, "Each area: forecast with range, epidemic threshold and history; alerts in English and Filipino", 11)

    open_page(page, "budget", replay=True)
    caption(page, "Budget plan: where each peso averts the most cases. Costs are editable; effects are cautious ranges", 11)

    open_page(page, "proof", replay=False)
    caption(page, "Tested honestly: every year forecast only from earlier years", 7)
    page.mouse.wheel(0, 700)
    caption(page, "Beat simple rules in 5 of 6 tests; caught most outbreak starts 4 weeks ahead", 9)
    page.mouse.wheel(0, 900)
    caption(page, "Weather adds little beyond case trends: it works with data LGUs already have", 9)

    open_page(page, "qc", replay=False)
    caption(page, "Quezon City: from a city forecast to a barangay shortlist", 9)
    caption(page, "github.com/Romeo-04/epilag", 5)

    video = page.video
    ctx.close()
    browser.close()
    target = OUT / "demo.webm"
    target.unlink(missing_ok=True)
    Path(video.path()).rename(target)
    print("saved", target)
