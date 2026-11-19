"""Short GIFs of the dashboard features (docs/screenshots/features/), recorded from the built site with Playwright.
Serve the build first (cd site && npx vite preview --port 4173), then: python scripts/pr_gifs.py [name ...]"""
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots" / "features"
BASE = "http://localhost:4173/epilag/"
W, H = 1280, 800

# a visible cursor (recordings do not show the real one), with a ring on click
CURSOR = """
addEventListener('DOMContentLoaded', () => {
  const c = document.createElement('div');
  c.style.cssText = 'position:fixed;z-index:2147483647;left:0;top:0;width:22px;height:22px;margin:-4px 0 0 -4px;pointer-events:none;transition:transform .08s;' +
    'background:url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E%3Cpath d=%27M1 1l5 14 2-6 6-2z%27 fill=%27%23071711%27 stroke=%27white%27 stroke-width=%271.2%27/%3E%3C/svg%3E") no-repeat';
  document.body.append(c);
  addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', (e) => {
    const r = document.createElement('div');
    r.style.cssText = `position:fixed;z-index:2147483646;left:${e.clientX - 16}px;top:${e.clientY - 16}px;width:32px;height:32px;border:3px solid #08754F;border-radius:50%;pointer-events:none;transition:all .4s;opacity:1`;
    document.body.append(r); requestAnimationFrame(() => { r.style.transform = 'scale(1.6)'; r.style.opacity = '0'; }); setTimeout(() => r.remove(), 500);
  }, true);
});
try { localStorage.setItem('el-guide', 'done'); sessionStorage.setItem('el-intro', '1'); } catch (e) {}
"""


def glide(pg, sel, pause=500):
    """Move the cursor smoothly onto an element."""
    box = pg.locator(sel).first.bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=18)
    pg.wait_for_timeout(pause)


def click(pg, sel, pause=900):
    glide(pg, sel, 250)
    pg.locator(sel).first.click()
    pg.wait_for_timeout(pause)


def scroll_to(pg, sel, offset=90, steps=14):
    """Smooth scroll so the element's top sits `offset` px below the top of the window."""
    y = pg.evaluate(f"document.querySelector({sel!r}).getBoundingClientRect().top") - offset
    for _ in range(steps):
        pg.mouse.wheel(0, y / steps)
        pg.wait_for_timeout(35)
    pg.wait_for_timeout(500)


def track_record(pg):
    pg.goto(BASE + "web/?page=unit&panel=region_qc&mode=latest&h=4&lang=en&region=R_NCR&area=QC"); pg.wait_for_timeout(1500)
    pg.mouse.move(700, 300)
    scroll_to(pg, ".track-grid", 120)
    glide(pg, ".track__big", 1200)
    glide(pg, "#card .rc-verdict__big", 900)
    glide(pg, "#card .rc-weeks tbody tr:nth-child(3) .rc-result", 900)
    click(pg, "#track .info-disclosure summary", 2200)
    click(pg, "#track .info-disclosure summary", 500)
    pg.mouse.wheel(0, -2000); pg.wait_for_timeout(600)
    glide(pg, "#c-h", 300)
    pg.select_option("#c-h", "8"); pg.wait_for_timeout(1500)
    scroll_to(pg, ".track-grid", 120)
    pg.wait_for_timeout(2200)


def reliability_sort(pg):
    pg.goto(BASE + "web/?page=home&lang=en"); pg.wait_for_timeout(1800)
    pg.mouse.move(900, 400)
    scroll_to(pg, ".overview-priority", 100)
    glide(pg, "#home-priority li:nth-child(1) .rel", 1100)
    click(pg, '#priority-sort button[data-v="reliable"]', 2200)
    glide(pg, "#home-priority li:nth-child(2) .rel", 1200)
    click(pg, '#priority-sort button[data-v="cases"]', 1800)


def report_card(pg):
    pg.goto(BASE + "web/?page=proof&lang=en"); pg.wait_for_timeout(1500)
    pg.mouse.move(700, 400)
    scroll_to(pg, "#report-card", 90, 20)
    pg.wait_for_timeout(800)
    glide(pg, "#report-card .rc-verdict__head", 1200)
    glide(pg, ".rc-table tbody tr:nth-child(5) .rc-miss", 1000)
    for _ in range(10):
        pg.mouse.wheel(0, 30); pg.wait_for_timeout(60)
    pg.wait_for_timeout(1500)


def print_report(pg):
    pg.goto(BASE + "web/?page=unit&panel=province&mode=replay&origin=2019-06-02&h=4&lang=en"); pg.wait_for_timeout(1800)
    pg.mouse.move(900, 300)
    click(pg, ".top-download", 900)
    glide(pg, "#top-download-1", 900)
    pg.keyboard.press("Escape")
    pg.evaluate("document.querySelector('.download-menu').open = false")
    pg.emulate_media(media="print")  # what the print dialog shows
    pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(2500)
    for _ in range(12):
        pg.mouse.wheel(0, 30); pg.wait_for_timeout(50)
    pg.wait_for_timeout(1800)
    pg.emulate_media(media="screen")


def offline(pg, ctx):
    pg.goto(BASE + "web/?page=home&lang=en"); pg.wait_for_timeout(1000)
    pg.evaluate("navigator.serviceWorker.ready")
    pg.wait_for_function("caches.keys().then(ks => ks.some(k => k.startsWith('epilag-')))", timeout=20000)
    pg.wait_for_timeout(800)
    ctx.set_offline(True)
    pg.mouse.move(600, 400)
    for view in ("unit", "public", "map"):
        click(pg, f'#tabs a[data-page="{view}"]', 2000)
    pg.reload(); pg.wait_for_timeout(2500)
    ctx.set_offline(False)
    pg.evaluate("dispatchEvent(new Event('online'))"); pg.wait_for_timeout(1800)


def sms(pg, ctx):
    ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE.rsplit("/epilag/", 1)[0])
    pg.goto(BASE + "web/?page=public&lang=en"); pg.wait_for_timeout(1500)
    pg.mouse.move(700, 400)
    scroll_to(pg, "#sms-card", 160, 20)
    glide(pg, "#sms", 1200)
    click(pg, "#copy-sms", 1300)
    glide(pg, "#send-sms", 900)
    pg.mouse.wheel(0, -3000); pg.wait_for_timeout(500)
    glide(pg, "#area", 300)
    pg.select_option("#area", "QC"); pg.wait_for_timeout(1000)
    click(pg, '#lang button[data-v="fil"]', 1200)
    scroll_to(pg, "#sms-card", 160, 20)
    glide(pg, "#sms", 2200)


def feeds(pg):
    pg.goto(BASE + "data/"); pg.wait_for_timeout(1500)
    pg.mouse.move(700, 400)
    scroll_to(pg, ".files", 70, 20)
    pg.mouse.wheel(0, 330); pg.wait_for_timeout(900)
    glide(pg, 'a[href="epilag_reliability_region_qc.csv"]', 1000)
    glide(pg, 'a[href="alerts.xml"]', 800)
    glide(pg, 'a[href="alerts.ics"]', 1000)
    scroll_to(pg, ".tbl--cols", 80, 20)
    glide(pg, ".tbl--cols tr:nth-child(9)", 2200)


SCENES = {"track-record": track_record, "reliability-sort": reliability_sort, "report-card": report_card,
          "print-report": print_report, "offline": offline, "sms": sms, "feeds": feeds}


def to_gif(video: Path, gif: Path, width=800, fps=10):
    pal = video.with_suffix(".png")
    vf = f"fps={fps},scale={width}:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.6", "-i", str(video), "-vf", f"{vf},palettegen=max_colors=80:stats_mode=diff", str(pal)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.6", "-i", str(video), "-i", str(pal), "-lavfi",
                    f"{vf}[x];[x][1:v]paletteuse=dither=none:diff_mode=rectangle", str(gif)], check=True)


def main(names):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
        b = p.chromium.launch()
        for name in names or SCENES:
            ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=tmp, record_video_size={"width": W, "height": H})
            ctx.add_init_script(CURSOR)
            pg = ctx.new_page()
            fn = SCENES[name]
            fn(pg, ctx) if fn.__code__.co_argcount == 2 else fn(pg)
            video = Path(pg.video.path())
            ctx.close()
            to_gif(video, OUT / f"{name}.gif")
            print(name, f"{(OUT / f'{name}.gif').stat().st_size / 1e6:.1f} MB")
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:])
