"""Render the showreel (docs/reel/index.html) to docs/showreel.mp4: 1920x1080, 30 fps, H.264 + AAC.

The page is a single seekable timeline, so the video is rendered frame by frame (render(t), then a screenshot),
never captured in real time: every frame is exact, however heavy the frame is. The soundtrack is mixed here:
the neural voice-over (python scripts/reel_voice.py), an original score synthesised to the reel's cues
(the dark rain-and-heartbeat opening, the brand hit, a tape-stop into the rewind, a groove for the product),
whooshes on every transition, and the music ducked under the voice.

Needs the live clips (python scripts/reel_capture.py), Chrome, and pip install playwright imageio-ffmpeg scipy.
Usage: python scripts/record_reel.py            the full film
       python scripts/record_reel.py --remix    a new soundtrack under the rendered video
       python scripts/record_reel.py --stills 3,40.5,88   PNG stills at those times, to check a frame
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
REEL = ROOT / "docs" / "reel" / "index.html"
OUT = ROOT / "docs" / "showreel.mp4"
SR = 44100


# ------------------------------------------------------------------ frames

def open_page(p):
    browser = p.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(REEL.as_uri() + "#record")
    page.wait_for_load_state("networkidle")
    page.evaluate("window.ready")
    if errors:
        raise SystemExit("page error: " + "; ".join(errors))
    return browser, page


def stills(times: list[float], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p)
        for t in sorted(times):  # the timeline renders forward, as it does in the film
            page.evaluate(f"render({t})")
            page.screenshot(path=out / f"t{t:06.2f}.png")
            print("saved", out / f"t{t:06.2f}.png")
        browser.close()


def frames(tmp: Path) -> dict:
    import base64
    with sync_playwright() as p:
        browser, page = open_page(p)
        reel = page.evaluate("REEL")
        cdp = page.context.new_cdp_session(page)
        n = int(reel["total"] * reel["fps"])
        for f in range(n):
            page.evaluate(f"render({f / reel['fps']})")
            shot = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 94, "optimizeForSpeed": True})
            (tmp / f"{f:05d}.jpg").write_bytes(base64.b64decode(shot["data"]))
            if f % 300 == 0:
                print(f"frame {f} / {n}", flush=True)
        browser.close()
    return reel


# ------------------------------------------------------------------ soundtrack (original, synthesised here)

def note(name: str) -> float:
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    return 440.0 * 2 ** ((names[name[0]] + ("#" in name) + 12 * (int(name[-1]) - 4)) / 12)


def env(n: int, attack: float, release: float) -> np.ndarray:
    tt = np.arange(n) / SR
    return np.clip(tt / attack, 0, 1) * np.clip((n / SR - tt) / release, 0, 1)


def lowpass(x, hz):
    return sosfilt(butter(2, hz, "low", fs=SR, output="sos"), x)


def highpass(x, hz):
    return sosfilt(butter(2, hz, "high", fs=SR, output="sos"), x)


def add(mix, start, sig):
    i = int(start * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    m = min(len(sig), len(mix) - i)
    if m > 0:
        mix[i:i + m] += sig[:m]


def kick(gain=1.0, dur=.35):
    tt = np.arange(int(dur * SR)) / SR
    return gain * np.sin(2 * np.pi * (45 * tt + 110 / 30 * (1 - np.exp(-tt * 30)))) * np.exp(-tt * 9)


def boom(gain=1.0):  # cinematic hit: sub drop and a noise crack
    tt = np.arange(int(3.0 * SR)) / SR
    rng = np.random.default_rng(5)
    sub = np.sin(2 * np.pi * (30 * tt + 70 / 4 * (1 - np.exp(-tt * 4)))) * np.exp(-tt * 1.6)
    crack = lowpass(rng.standard_normal(len(tt)), 3000) * np.exp(-tt * 14)
    return gain * (0.9 * sub + 0.35 * crack)


def whoosh(dur=0.9, seed=0):
    rng = np.random.default_rng(seed)
    m = int(dur * SR)
    noise = rng.standard_normal(m)
    out = np.concatenate([lowpass(noise[c:c + 1024], 300 + 6000 * np.sin(np.pi * c / m) ** 2) for c in range(0, m, 1024)])[:m]
    return out * np.sin(np.pi * np.arange(m) / m) ** 2


def soundtrack(reel: dict) -> np.ndarray:
    total, cues = reel["total"], reel["cues"]
    brand, play, end = reel["brand"], reel["play"], reel["end"]
    n = int((total + 0.5) * SR)
    t = np.arange(n) / SR
    music = np.zeros(n)
    sfx = np.zeros(n)
    rng = np.random.default_rng(7)

    # 1. the dark opening: an A-minor drone that swells into the brand
    drone = sum(np.sin(2 * np.pi * f * t + ph) for f, ph in [(55, 0), (82.4, 1), (110, 2), (130.8, .4), (164.8, .5)])
    drone *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.09 * t) ** 2
    music += 0.05 * drone * np.clip((brand + 0.3 - t) / 1.2, 0, 1) * np.clip(t / 2.5, 0, 1)

    # 2. rain under the first two scenes, with thunder at the lightning flashes
    rain = highpass(lowpass(rng.standard_normal(n), 5200), 400) * np.clip((16.6 - t) / 1.5, 0, 1) * np.clip(t / 1.0, 0, 1)
    sfx += 0.05 * rain
    for f in (0.5, 3.9):
        add(sfx, f, 0.35 * lowpass(rng.standard_normal(int(2.5 * SR)), 180) * np.exp(-np.arange(int(2.5 * SR)) / SR * 1.8))

    # 3. a mosquito whine as the swarm doubles, then heartbeats through the surge and the lag
    sw = (t > 13.2) & (t < 16.8)
    whine = np.sin(2 * np.pi * (560 + 40 * np.sin(2 * np.pi * 7 * t)) * t) * np.clip((t - 13.2) / 3, 0, 1) * np.clip((16.8 - t) / .3, 0, 1)
    sfx += 0.03 * whine * sw
    beat_t = 17.0
    while beat_t < brand - 0.5:
        for k, dt in enumerate((0, 0.2)):
            add(music, beat_t + dt, kick(0.34 if k == 0 else 0.22))
        beat_t += 1.15 - 0.45 * (beat_t - 17) / (brand - 17)  # the pulse quickens toward the reveal

    # 4. risers into the reveal and into the drill cut
    for a, b in cues["riser"]:
        m = int((b - a) * SR)
        tt = np.arange(m) / SR
        k = tt / (b - a)
        tone = np.sin(2 * np.pi * (200 * tt + 900 * tt * k / 2)) * k ** 2
        noise = np.concatenate([lowpass(rng.standard_normal(1024), 500 + 7000 * (c / m) ** 2) for c in range(0, m, 1024)])[:m] * k ** 2
        add(sfx, a, 0.06 * tone + 0.16 * noise)

    # 5. the brand: a big hit and a warm major pad that holds until the tape stops
    for c in cues["impact"]:
        add(sfx, c, boom(0.55 if c in (brand + 1.35, play) else 0.4))
    for c in cues["tick"]:
        add(sfx, c, kick(0.28, .25) + 0.05 * highpass(rng.standard_normal(int(.25 * SR)), 4000) * np.exp(-np.arange(int(.25 * SR)) / SR * 30))
    m = int((cues["tape"][0] - brand) * SR)
    tt = np.arange(m) / SR
    pad = sum(np.sin(2 * np.pi * note(x) * tt) + 0.25 * np.sin(2 * np.pi * 2 * note(x) * tt) for x in ["F3", "A3", "C4", "E4"])
    add(music, brand, 0.05 * pad * env(m, 0.8, 0.15))

    # 6. tape stop, then a reversed swell that lands on PLAY
    stop = cues["tape"][0]
    m = int(0.7 * SR)
    tt = np.arange(m) / SR
    add(sfx, stop, 0.3 * np.sin(2 * np.pi * (220 * tt - 150 * tt ** 2)) * np.exp(-tt * 3))
    m = int((play - stop) * SR)
    tt = np.arange(m) / SR
    rev = (lowpass(rng.standard_normal(m), 6000) * 0.12 + 0.05 * sum(np.sin(2 * np.pi * note(x) * tt) for x in ["A3", "C4", "E4"])) * (tt / tt[-1]) ** 3
    add(music, stop, rev)

    # 7. the groove from PLAY to the end card, tempo set so the drill cut lands on a downbeat
    beat = 40.5 / 68
    chords = [["A2", "A3", "C4", "E4"], ["F2", "F3", "A3", "C4"], ["C3", "C4", "E4", "G4"], ["G2", "G3", "B3", "D4"]]
    drill_a, drill_b = 85.6, 93.4
    k = 0
    for start in np.arange(play, end, 4 * beat):
        ch, k = chords[k % 4], k + 1
        m = int(4 * beat * SR)
        tt = np.arange(m) / SR
        energy = 1.25 if drill_a - 0.01 <= start < drill_b else 0.6 if 80.4 <= start < drill_a else 1.0
        padsig = sum(np.sin(2 * np.pi * note(x) * tt) + 0.3 * np.sin(2 * np.pi * 2.003 * note(x) * tt) for x in ch[1:])
        add(music, start, 0.04 * padsig * env(m, 0.3, 0.4))
        add(music, start, 0.09 * np.sin(2 * np.pi * note(ch[0]) * tt) * env(m, 0.02, 0.3))
        if start < play + 4 * beat - 0.01 or 80.4 <= start < drill_a:  # first bar and the drill's build: pads only
            continue
        for j in range(8):
            s = start + j * beat / 2
            f = note(ch[1 + j % 3]) * (2 if j % 2 else 1)
            pm = int(0.25 * SR)
            pt = np.arange(pm) / SR
            add(music, s, energy * 0.045 * np.sin(2 * np.pi * f * pt) * np.exp(-pt * 13))
            if j % 2 == 0:
                add(music, s, kick(0.3 * energy))
            else:
                hm = int(0.06 * SR)
                add(music, s, 0.03 * energy * highpass(rng.standard_normal(hm), 6000) * np.exp(-np.arange(hm) / SR * 70))
            if energy > 1 and j in (2, 6):  # snare on 2 and 4 in the drill
                sm = int(0.2 * SR)
                add(music, s, 0.12 * highpass(rng.standard_normal(sm), 1500) * np.exp(-np.arange(sm) / SR * 18))

    # 8. end card: one last chord that rings out
    m = int((total - end + 0.5) * SR)
    tt = np.arange(m) / SR
    final = sum(np.sin(2 * np.pi * note(x) * tt) + 0.3 * np.sin(2 * np.pi * 2 * note(x) * tt) for x in ["A2", "E3", "A3", "C#4", "E4"])
    add(music, end, 0.06 * final * np.exp(-tt * 0.35))

    # transitions
    for i, c in enumerate(cues["whoosh"]):
        add(sfx, c - 0.55, 0.16 * whoosh(0.9, i))
    for c in cues["glitch"]:
        m = int(0.35 * SR)
        g = np.repeat(rng.standard_normal(m // 40 + 1), 40)[:m]
        add(sfx, c, 0.18 * g * np.sign(np.sin(2 * np.pi * 60 * np.arange(m) / SR)))

    # the voice, with the music ducked under it
    voice = np.zeros(n)
    for v in reel["vo"]:
        sr, x = wavfile.read(ROOT / "docs" / "reel" / "vo" / f"{v['id']}.wav")
        x = x.astype(np.float64) / 32768.0
        add(voice, v["at"], x)
    level = np.abs(voice)
    win = int(0.25 * SR)
    c = np.concatenate([[0], np.cumsum(level)])
    level = (c[np.clip(np.arange(n) + win // 2, 0, n)] - c[np.clip(np.arange(n) - win // 2, 0, n)]) / win  # moving average
    duck = 1 - 0.55 * np.clip(level / 0.04, 0, 1)
    mix = (music * 1.25) * duck + sfx * (0.6 + 0.4 * duck) + voice * 1.15
    mix *= np.clip(t / 0.3, 0, 1) * np.clip((total - t) / 1.6, 0, 1)
    mix = np.tanh(mix * 1.2)
    return (mix / np.abs(mix).max() * 0.9).astype(np.float32)


def main() -> None:
    if "--remix" in sys.argv:  # new soundtrack under the existing video, without rendering the frames again
        with sync_playwright() as p:
            browser, page = open_page(p)
            reel = page.evaluate("REEL")
            browser.close()
        tmp = Path(tempfile.mkdtemp(prefix="epilag_reel_"))
        try:
            wavfile.write(tmp / "mix.wav", SR, np.stack([soundtrack(reel)] * 2, axis=1))
            shutil.copy(OUT, tmp / "video.mp4")
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(tmp / "video.mp4"), "-i", str(tmp / "mix.wav"),
                            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(OUT)], check=True)
            print("remixed", OUT.relative_to(ROOT))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return
    if "--stills" in sys.argv:
        times = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        stills(times, Path(sys.argv[sys.argv.index("--stills") + 2]) if len(sys.argv) > sys.argv.index("--stills") + 2 else ROOT / "reel_stills")
        return
    tmp = Path(tempfile.mkdtemp(prefix="epilag_reel_"))
    try:
        reel = frames(tmp)
        audio = soundtrack(reel)
        wavfile.write(tmp / "mix.wav", SR, np.stack([audio, audio], axis=1))
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(reel["fps"]), "-i", str(tmp / "%05d.jpg"),
                        "-i", str(tmp / "mix.wav"), "-vf", "scale=out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(OUT)], check=True)
        print("saved", OUT.relative_to(ROOT), f"{OUT.stat().st_size / 1e6:.1f} MB")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
