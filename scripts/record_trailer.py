"""Render the trailer (docs/reel/trailer/index.html) to MP4, landscape and portrait: 30 fps, H.264 + AAC.

  landscape  1920 x 1080   docs/reel/trailer/out/epilag-trailer-land.mp4
  portrait   1080 x 1920   docs/reel/trailer/out/epilag-trailer-port.mp4   (Instagram Reels)

The page is one seekable timeline laid out for both frames, so each video is rendered frame by frame
(render(t), then a screenshot). The soundtrack is mixed here, as in scripts/record_reel.py: the voice-over
(python scripts/trailer_voice.py), an original score synthesised to the trailer's cues (rain and a drone for
the cold open, a hit on every title card, a groove under the product, a harder one under the Dengue Drill
montage), whooshes on the cuts, and the music ducked under the voice.

Needs the clips (python scripts/trailer_capture.py), Chrome, and pip install playwright imageio-ffmpeg scipy.
The landscape is one pass. The portrait is two: the picture alone (index.html?pic, 1920 x 1080, to out/pic/),
then the portrait page, which shows those frames as a band over their own blur with the type stacked around it.

Usage: python scripts/record_trailer.py [land|port|both] [--no-voice]     both is the default
       python scripts/record_trailer.py port --remix                      a new soundtrack under the rendered video
       python scripts/record_trailer.py port --keep-pic                   reuse (and keep) the picture frames in out/pic/
       python scripts/record_trailer.py land --stills 3,40.5,88 [folder]  PNG stills at those times
       (portrait stills: run `pic --stills` with the same times first)
"""
import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_reel import SR, add, boom, env, highpass, kick, lowpass, note, whoosh  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "reel" / "trailer" / "index.html"
OUT = PAGE.parent / "out"
SIZE = {"land": (1920, 1080), "port": (1080, 1920), "pic": (1920, 1080)}
PIC = OUT / "pic"  # the picture alone, frame by frame: the portrait cut shows it as a band over its own blur
VOICE_ON = "--no-voice" not in sys.argv


QUERY = {"land": "", "port": "?port", "pic": "?pic"}


def open_page(p, fmt):
    w, h = SIZE[fmt]
    browser = p.chromium.launch(args=["--allow-file-access-from-files"])
    page = browser.new_page(viewport={"width": w, "height": h})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(PAGE.as_uri() + QUERY[fmt] + "#record")
    page.wait_for_load_state("networkidle")
    page.evaluate("window.ready")
    if errors:
        raise SystemExit("page error: " + "; ".join(errors))
    return browser, page


def stills(fmt, times, out):
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p, fmt)
        for t in sorted(times):  # the timeline renders forward, as it does in the film
            page.evaluate(f"render({t})")
            if fmt == "pic":  # saved where the portrait page looks for it
                PIC.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=PIC / f"{round(t * 30):05d}.jpg", type="jpeg", quality=90)
            page.screenshot(path=out / f"{fmt}_{t:06.2f}.png")
        print("saved", len(times), "stills in", out, "· total", page.evaluate("TOTAL"), "s")
        browser.close()


def frames(fmt, tmp):
    with sync_playwright() as p:
        browser, page = open_page(p, fmt)
        reel = page.evaluate("REEL")
        cdp = page.context.new_cdp_session(page)
        n = int(reel["total"] * reel["fps"])
        for f in range(n):
            page.evaluate(f"render({f / reel['fps']})")
            shot = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 90 if fmt == "pic" else 94, "optimizeForSpeed": True})
            (tmp / f"{f:05d}.jpg").write_bytes(base64.b64decode(shot["data"]))
            if f % 300 == 0:
                print(f"{fmt}: frame {f} / {n}", flush=True)
        browser.close()
    return reel


# ------------------------------------------------------------------ soundtrack (original, synthesised here)

def soundtrack(reel, voice_on=True):
    total, cues, M = reel["total"], reel["cues"], reel["marks"]
    n = int((total + 0.5) * SR)
    t = np.arange(n) / SR
    music, sfx = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(7)
    between = lambda a, b, fi=.4, fo=.4: np.clip((t - a) / fi, 0, 1) * np.clip((b - t) / fo, 0, 1)

    # 1. cold open: rain, thunder on the lightning, an A-minor drone that swells to the brand
    noise = highpass(lowpass(rng.standard_normal(n), 5200), 400)
    sfx += 0.055 * noise * between(0, M["surge"] + .3, 1.0, 1.2)
    sfx += 0.045 * noise * between(M["again"], M["end"] + .6, .8, 1.2)
    a, b = M["mosq"], M["surge"]  # a mosquito whine as the swarm doubles and rushes the camera
    whine = np.sin(2 * np.pi * (560 + 40 * np.sin(2 * np.pi * 7 * t)) * t) * np.clip((t - a) / 2.5, 0, 1) * np.clip((b - t) / .3, 0, 1)
    sfx += 0.035 * whine * ((t > a) & (t < b))
    for f in (0.4, M["hookLine"], M["again"] + 2.6):
        m = int(2.5 * SR)
        add(sfx, f, 0.34 * lowpass(rng.standard_normal(m), 180) * np.exp(-np.arange(m) / SR * 1.8))
    drone = sum(np.sin(2 * np.pi * f * t + ph) for f, ph in [(55, 0), (82.4, 1), (110, 2), (130.8, .4), (164.8, .5)])
    drone *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.09 * t) ** 2
    music += 0.055 * drone * between(0, M["brand"] + .3, 2.5, 1.2)

    # 2. heartbeats that quicken from the surge to the question
    bt, b0, b1 = M["surge"] + .3, M["surge"] + .3, M["brand"] - .5
    while bt < b1:
        for k, dt in enumerate((0, 0.2)):
            add(music, bt + dt, kick(0.36 if k == 0 else 0.24))
        bt += 1.2 - 0.6 * (bt - b0) / (b1 - b0)

    # 3. risers, hits and ticks
    for a, b in cues["riser"]:
        m = int((b - a) * SR)
        tt = np.arange(m) / SR
        k = tt / (b - a)
        tone = np.sin(2 * np.pi * (200 * tt + 900 * tt * k / 2)) * k ** 2
        nz = np.concatenate([lowpass(rng.standard_normal(1024), 500 + 7000 * (c / m) ** 2) for c in range(0, m, 1024)])[:m] * k ** 2
        add(sfx, a, 0.03 * tone + 0.06 * nz)
    for c in cues["impact"]:
        add(sfx, c, boom(0.3))
    for c in cues["tick"]:
        m = int(.25 * SR)
        add(sfx, c, kick(0.13, .25) + 0.025 * highpass(rng.standard_normal(m), 4000) * np.exp(-np.arange(m) / SR * 30))

    # 4. the brand: a warm major chord that holds until the product starts
    stop, play = cues["tape"][0], M["play"]
    m = int((stop - M["brand"]) * SR)
    tt = np.arange(m) / SR
    pad = sum(np.sin(2 * np.pi * note(x) * tt) + 0.25 * np.sin(2 * np.pi * 2 * note(x) * tt) for x in ["F3", "A3", "C4", "E4"])
    add(music, M["brand"], 0.055 * pad * env(m, 0.6, 0.15))
    # tape stop, a reversed swell that lands on PLAY, then a held chord under the replay
    m = int(0.7 * SR)
    tt = np.arange(m) / SR
    add(sfx, stop, 0.15 * np.sin(2 * np.pi * (220 * tt - 150 * tt ** 2)) * np.exp(-tt * 3))
    m = int((play - stop) * SR)
    tt = np.arange(m) / SR
    rev = (lowpass(rng.standard_normal(m), 6000) * 0.12 + 0.05 * sum(np.sin(2 * np.pi * note(x) * tt) for x in ["A3", "C4", "E4"])) * (tt / tt[-1]) ** 3
    add(music, stop, rev)
    m = int((M["sizzle"] - play + .2) * SR)
    tt = np.arange(m) / SR
    hold = sum(np.sin(2 * np.pi * note(x) * tt) + 0.3 * np.sin(2 * np.pi * 2.003 * note(x) * tt) for x in ["A2", "A3", "C4", "E4"]) + 0.5 * np.sin(2 * np.pi * note("G4") * tt) * (tt / tt[-1])
    add(music, play, 0.045 * hold * env(m, 0.3, 0.3))
    pulse = play + 1.0
    while pulse < M["sizzle"] - .2:
        add(music, pulse, kick(0.22))
        pulse += 0.56

    # 5. the groove, from the first chapter to the end of the montage. It thins out under the research,
    #    stops for each title card, and comes back hardest for the game.
    g0, g1 = M["sizzle"], M["again"]
    bars = max(1, round((g1 - g0) / (4 * 0.56)))
    beat = (g1 - g0) / (bars * 4)
    chords = [["A2", "A3", "C4", "E4"], ["F2", "F3", "A3", "C4"], ["C3", "C4", "E4", "G4"], ["G2", "G3", "B3", "D4"]]
    quiet = [(M["test"] - .2, M["test2"]), (M["losses"] - .2, M["losses2"]), (M["drill"] - .2, M["drill2"])]

    def energy(s):
        if any(a <= s < b for a, b in quiet):
            return 0.0
        if s >= M["montage"] - .05 or s < M["see"] - .05:
            return 1.5
        if s >= M["drill2"]:
            return 1.2
        if s >= M["test"]:
            return 0.75
        return 1.0

    for k, start in enumerate(np.arange(g0, g1 - 0.01, 4 * beat)):
        ch = chords[k % 4]
        m = int(min(4 * beat, g1 + .3 - start) * SR)
        tt = np.arange(m) / SR
        padsig = sum(np.sin(2 * np.pi * note(x) * tt) + 0.3 * np.sin(2 * np.pi * 2.003 * note(x) * tt) for x in ch[1:])
        add(music, start, 0.04 * padsig * env(m, 0.3, 0.4))
        add(music, start, 0.09 * np.sin(2 * np.pi * note(ch[0]) * tt) * env(m, 0.02, 0.3))
        for j in range(8):
            s_ = start + j * beat / 2
            e = energy(s_)
            if s_ > g1 or e == 0:
                continue
            f = note(ch[1 + j % 3]) * (2 if j % 2 else 1)
            pt = np.arange(int(0.25 * SR)) / SR
            add(music, s_, e * 0.045 * np.sin(2 * np.pi * f * pt) * np.exp(-pt * 13))
            if j % 2 == 0:
                add(music, s_, kick(0.3 * min(e, 1.3)))
            else:
                hm = int(0.06 * SR)
                add(music, s_, 0.03 * e * highpass(rng.standard_normal(hm), 6000) * np.exp(-np.arange(hm) / SR * 70))
            if e > 1.1 and j in (2, 6):
                sm = int(0.2 * SR)
                add(music, s_, 0.12 * (e - .3) * highpass(rng.standard_normal(sm), 1500) * np.exp(-np.arange(sm) / SR * 18))
            if e > 1.4 and j % 2:  # the montage doubles the hats
                hm = int(0.04 * SR)
                add(music, s_ + beat / 4, 0.025 * highpass(rng.standard_normal(hm), 7000) * np.exp(-np.arange(hm) / SR * 90))

    # 6. the rains again: a quiet pad, then one last chord that rings out under the end card
    end = M["end"]
    m = int((end - M["again"]) * SR)
    tt = np.arange(m) / SR
    soft = sum(np.sin(2 * np.pi * note(x) * tt) for x in ["A2", "E3", "C4"]) * 0.6 + sum(np.sin(2 * np.pi * note(x) * tt) for x in ["F2", "C3", "A3"]) * 0.4 * (tt / tt[-1])
    add(music, M["again"], 0.045 * soft * env(m, 0.8, 0.4))
    m = int((total - end + 0.5) * SR)
    tt = np.arange(m) / SR
    final = sum(np.sin(2 * np.pi * note(x) * tt) + 0.3 * np.sin(2 * np.pi * 2 * note(x) * tt) for x in ["A2", "E3", "A3", "C#4", "E4"])
    add(music, end + .1, 0.06 * final * np.exp(-tt * 0.35))

    # cuts
    for i, c in enumerate(cues["whoosh"]):
        add(sfx, c - 0.55, 0.04 * whoosh(0.9, i))
    for c in cues["glitch"]:
        m = int(0.32 * SR)
        g = np.repeat(rng.standard_normal(m // 40 + 1), 40)[:m]
        add(sfx, c, 0.07 * g * np.sign(np.sin(2 * np.pi * 60 * np.arange(m) / SR)))

    # the voice, with the music ducked under it (without the voice, the music still dips where it will go)
    voice = np.zeros(n)
    for v in reel["vo"]:
        sr, x = wavfile.read(PAGE.parent / "vo" / f"{v['id']}.wav")
        x = x.astype(np.float64) / 32768.0
        if x.ndim > 1:
            x = x.mean(axis=1)
        add(voice, v["at"], x)
    level = np.abs(voice)
    win = int(0.25 * SR)
    c = np.concatenate([[0], np.cumsum(level)])
    level = (c[np.clip(np.arange(n) + win // 2, 0, n)] - c[np.clip(np.arange(n) - win // 2, 0, n)]) / win
    duck = 1 - 0.55 * np.clip(level / 0.04, 0, 1)
    mix = (music * 1.25) * duck + sfx * (0.6 + 0.4 * duck) + (voice * 1.15 if voice_on else 0)
    mix *= np.clip(t / 0.3, 0, 1) * np.clip((total - t) / 1.6, 0, 1)
    mix = np.tanh(mix * 1.2)
    return (mix / np.abs(mix).max() * 0.9).astype(np.float32)


def render(fmt):
    out = OUT / f"epilag-trailer-{fmt}.mp4"
    OUT.mkdir(parents=True, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    tmp = Path(tempfile.mkdtemp(prefix=f"epilag_trailer_{fmt}_"))
    try:
        if "--remix" in sys.argv:  # a new soundtrack under the existing video, without rendering the frames again
            with sync_playwright() as p:
                browser, page = open_page(p, fmt)
                reel = page.evaluate("REEL")
                browser.close()
            audio = soundtrack(reel, VOICE_ON)
            wavfile.write(tmp / "mix.wav", SR, np.stack([audio, audio], axis=1))
            shutil.copy(out, tmp / "video.mp4")
            subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp / "video.mp4"), "-i", str(tmp / "mix.wav"), "-map", "0:v", "-map", "1:a",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
        else:
            if fmt == "port" and "--keep-pic" not in sys.argv:
                shutil.rmtree(PIC, ignore_errors=True)
                PIC.mkdir(parents=True)
                frames("pic", PIC)
            reel = frames(fmt, tmp)
            audio = soundtrack(reel, VOICE_ON)
            wavfile.write(tmp / "mix.wav", SR, np.stack([audio, audio], axis=1))
            subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(reel["fps"]), "-i", str(tmp / "%05d.jpg"), "-i", str(tmp / "mix.wav"),
                            "-vf", "scale=out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
        print("saved", out, f"{out.stat().st_size / 1e6:.1f} MB")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if fmt == "port" and "--keep-pic" not in sys.argv and "--remix" not in sys.argv:
            shutil.rmtree(PIC, ignore_errors=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fmts = ["land", "port"] if not args or args[0] == "both" else [args[0]]
    if "--stills" in sys.argv:
        i = sys.argv.index("--stills")
        times = [float(x) for x in sys.argv[i + 1].split(",")]
        folder = Path(sys.argv[i + 2]) if len(sys.argv) > i + 2 and not sys.argv[i + 2].startswith("--") else ROOT / "reel_stills"
        for fmt in fmts:
            stills(fmt, times, folder)
        return
    for fmt in fmts:
        render(fmt)


if __name__ == "__main__":
    main()
