"""Render the system-flow video (docs/reel/flow/index.html) to MP4: 1920 x 1080, 30 fps, H.264 + AAC.

  docs/reel/flow/out/epilag-flow-guide.mp4   with the guide voice (the pace the video is cut to)
  docs/reel/flow/out/epilag-flow.mp4         music and sound effects only, to narrate over

The page is one seekable timeline: each frame is render(t), then a screenshot. The soundtrack is synthesised here,
as in scripts/record_reel.py: a light original music bed, a soft tick whenever data reaches a node,
a chime on the Watch alert and a hit on the result. Under the guide voice the music ducks.

Needs the voice (python scripts/flow_voice.py --own <recording>, or the ElevenLabs one), the page assets (node scripts/flow_assets.mjs), the captures
of the app and game (python scripts/flow_capture.py), Chrome, and pip install playwright imageio-ffmpeg scipy.

Usage: python scripts/record_flow.py                       both cuts
       python scripts/record_flow.py --remix               new soundtracks under the rendered picture (out/picture.mp4)
       python scripts/record_flow.py --stills 3,40.5 [dir] PNG stills at those times
"""
import base64
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_reel import SR, add, boom, env, highpass, kick, lowpass, note  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "reel" / "flow" / "index.html"
OUT = PAGE.parent / "out"
FF = imageio_ffmpeg.get_ffmpeg_exe()


def open_page(p):
    browser = p.chromium.launch(args=["--allow-file-access-from-files"])
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(PAGE.as_uri() + "#record")
    page.wait_for_load_state("networkidle")
    page.evaluate("window.ready")
    if errors:
        raise SystemExit("page error: " + "; ".join(errors))
    return browser, page


def stills(times, out):
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p)
        for t in sorted(times):
            page.evaluate(f"render({t})")
            page.screenshot(path=out / f"flow_{t:06.2f}.png")
        print("saved", len(times), "stills in", out, "· total", page.evaluate("TOTAL"), "s")
        browser.close()


def frames(tmp):
    with sync_playwright() as p:
        browser, page = open_page(p)
        reel = page.evaluate("REEL")
        cdp = page.context.new_cdp_session(page)
        n = int(reel["total"] * reel["fps"])
        for f in range(n):
            page.evaluate(f"render({f / reel['fps']})")
            shot = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 95, "optimizeForSpeed": True})
            (tmp / f"{f:05d}.jpg").write_bytes(base64.b64decode(shot["data"]))
            if f % 300 == 0:
                print(f"frame {f} / {n}", flush=True)
        browser.close()
    return reel


def reel_info():
    with sync_playwright() as p:
        browser, page = open_page(p)
        reel = page.evaluate("REEL")
        browser.close()
    return reel


# ------------------------------------------------------------------ soundtrack (original, synthesised here)

def tick(gain, pitch):  # a soft glassy blip: data arriving at a node
    tt = np.arange(int(.22 * SR)) / SR
    return gain * (np.sin(2 * np.pi * pitch * tt) + .35 * np.sin(2 * np.pi * 2 * pitch * tt)) * np.exp(-tt * 26)


def chime(gain=1.0):  # the Watch alert: two bright notes
    out = np.zeros(int(1.6 * SR))
    for k, (name, dt) in enumerate((("E5", 0), ("A5", .11))):
        tt = np.arange(len(out) - int(dt * SR)) / SR
        add(out, dt, (np.sin(2 * np.pi * note(name) * tt) + .3 * np.sin(2 * np.pi * 3 * note(name) * tt)) * np.exp(-tt * 3.2) * (1 - .25 * k))
    return gain * out


def music(total, reel):
    """A calm, bright bed at 100 bpm: soft pads, a plucked arpeggio and a light pulse. Quiet on the title,
    full through the steps, and a held chord under the result."""
    n = int((total + 1) * SR)
    t = np.arange(n) / SR
    mix = np.zeros(n)
    rng = np.random.default_rng(11)
    beat = 60 / 100
    vo = {v["id"]: v["at"] for v in reel["vo"]}
    start, close = vo["system"] - 4 * beat, vo["close"]
    chords = [["F2", "A3", "C4", "E4"], ["A2", "C4", "E4", "G4"], ["C3", "E4", "G4", "B4"], ["G2", "B3", "D4", "G4"]]
    # intro: a soft swell on the first chord
    m = int(start * SR) + SR
    tt = np.arange(m) / SR
    add(mix, 0, .05 * sum(np.sin(2 * np.pi * note(x) * tt) for x in chords[0][1:]) * env(m, 1.5, .8))
    bar = 4 * beat
    k = 0
    for s in np.arange(start, close, bar):
        ch = chords[k % 4]
        k += 1
        m = int(min(bar + .4, close + .6 - s) * SR)
        tt = np.arange(m) / SR
        pad = sum(np.sin(2 * np.pi * note(x) * tt) + .25 * np.sin(2 * np.pi * 2.004 * note(x) * tt) for x in ch[1:])
        add(mix, s, .032 * pad * env(m, .25, .45))
        add(mix, s, .07 * np.sin(2 * np.pi * note(ch[0]) * tt) * env(m, .03, .4))
        for j in range(8):  # eighth-note arpeggio
            at = s + j * beat / 2
            if at >= close:
                break
            f = note(ch[1 + (j * 2) % 3]) * (2 if j % 4 == 3 else 1)
            pt = np.arange(int(.3 * SR)) / SR
            add(mix, at, .03 * np.sin(2 * np.pi * f * pt) * np.exp(-pt * 11))
            if j % 2 == 0:
                add(mix, at, kick(.16 if j % 4 == 0 else .08, .25))
            else:
                hm = int(.05 * SR)
                add(mix, at, .012 * highpass(rng.standard_normal(hm), 7000) * np.exp(-np.arange(hm) / SR * 80))
    # the result: a held, opening chord to the end
    m = int((total - close + .8) * SR)
    tt = np.arange(m) / SR
    held = sum(np.sin(2 * np.pi * note(x) * tt) + .3 * np.sin(2 * np.pi * 2.003 * note(x) * tt) for x in ["F2", "C4", "F4", "A4", "E5"])
    add(mix, close - .1, .045 * held * env(m, .4, 1.4))
    return mix


def sfx_track(total, cues):
    n = int((total + 1) * SR)
    out = np.zeros(n)
    last = -1
    for k, c in enumerate(sorted(cues["tick"])):
        if c - last < .06:
            continue
        last = c
        add(out, c, tick(.09, [1318.5, 1568.0, 1760.0][k % 3]))
    for c in cues["chime"]:
        add(out, c, chime(.08))
    for c in cues["hit"]:
        add(out, c, boom(.12))
    return out


def voice_track(total, reel):
    n = int((total + 1) * SR)
    out, speaking = np.zeros(n), np.zeros(n)
    for v in reel["vo"]:
        sr, x = wavfile.read(PAGE.parent / "vo" / f"{v['id']}.wav")
        x = x.astype(np.float64) / 32768
        add(out, v["at"], x)
        a, b = int(v["at"] * SR), int((v["at"] + v["dur"]) * SR)
        speaking[a:b] = 1
    k = int(.25 * SR)  # smooth the ducking envelope
    speaking = np.convolve(speaking, np.ones(k) / k, mode="same")
    return out, speaking


def master(x, level=.89):
    x = x - np.mean(x)
    peak = np.max(np.abs(x)) or 1
    return np.int16(np.clip(x / peak * level, -1, 1) * 32767)


def soundtracks(reel):
    total = reel["total"]
    bed, fx = music(total, reel), sfx_track(total, reel["cues"])
    voice, speaking = voice_track(total, reel)
    guide = voice * 1.0 + bed * (1 - .55 * speaking) + fx * .8
    clean = bed * .8 + fx  # steady, so a voice recorded over it sits on top
    return {"guide": master(guide), "clean": master(clean, .3)}  # the clean bed peaks near -10 dB, under a voice


def mux(picture, wav, out):
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(picture), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("saved", out.relative_to(ROOT))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if "--stills" in sys.argv:
        i = sys.argv.index("--stills")
        times = [float(x) for x in sys.argv[i + 1].split(",")]
        folder = Path(sys.argv[i + 2]) if len(sys.argv) > i + 2 else OUT / "stills"
        return stills(times, folder)
    picture = OUT / "picture.mp4"
    if "--remix" in sys.argv:
        reel = reel_info()
    else:
        with tempfile.TemporaryDirectory() as tmp:
            reel = frames(Path(tmp))
            subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(reel["fps"]), "-i", str(Path(tmp) / "%05d.jpg"),
                            "-vf", "scale=in_range=full:out_range=tv", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-color_range", "tv", "-movflags", "+faststart", str(picture)], check=True)
    tracks = soundtracks(reel)
    for name, data in tracks.items():
        wav = OUT / f"{name}.wav"
        wavfile.write(wav, SR, data)
        mux(picture, wav, OUT / ("epilag-flow-guide.mp4" if name == "guide" else "epilag-flow.mp4"))
        wav.unlink()


if __name__ == "__main__":
    main()
