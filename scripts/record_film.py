"""Record the motion-graphics film (docs/film/index.html) to docs/demo.mp4, with a generated soundtrack.

Captures Chrome's screencast frames in real time (JPEG, high quality), rebuilds them at a constant 30 fps,
synthesises an original music bed timed to the scene changes, and encodes H.264 + AAC with ffmpeg
(pip install imageio-ffmpeg). Needs Chrome, ~600 MB of free disk for the temporary frames, and the
screenshots in docs/screenshots (python scripts/screenshots.py). No voice-over: the on-screen text tells the story.

Usage: python scripts/record_film.py
"""
import base64
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / "docs" / "film" / "index.html"
OUT = ROOT / "docs" / "demo.mp4"
FPS, SR = 30, 44100


# ------------------------------------------------------------------ capture

def capture(tmp: Path) -> tuple[list[tuple[float, Path]], float, float]:
    """Return [(timestamp, frame path)], the play start time and the film length, all in seconds."""
    frames = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(FILM.as_uri() + "#manual")
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready.then(() => Promise.all([...document.images].map(i => i.decode())))")
        total = page.evaluate("TOTAL")
        cdp = page.context.new_cdp_session(page)

        def on_frame(ev):
            ts = ev["metadata"]["timestamp"]
            path = tmp / f"f{len(frames):05d}.jpg"
            path.write_bytes(base64.b64decode(ev["data"]))
            frames.append((ts, path))
            try:
                cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
            except Exception:  # the page closed while a last frame was in flight
                pass

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1920, "maxHeight": 1080})
        page.wait_for_timeout(1000)
        start = time.time()
        page.evaluate("play()")
        deadline = start + total + 1.0
        while time.time() < deadline:
            page.wait_for_timeout(50)
        cdp.send("Page.stopScreencast")
        browser.close()
    return frames, start, total


def to_video(frames, start: float, total: float, tmp: Path) -> Path:
    """Constant-frame-rate video: for each output tick, the latest screencast frame."""
    ts = np.array([t for t, _ in frames])
    ticks = start + np.arange(int(total * FPS)) / FPS
    idx = np.clip(np.searchsorted(ts, ticks, side="right") - 1, 0, len(frames) - 1)
    lines = []
    for i in idx:
        lines += [f"file '{frames[i][1].as_posix()}'", f"duration {1 / FPS:.6f}"]
    (tmp / "frames.txt").write_text("\n".join(lines) + "\n")
    return tmp / "frames.txt"


# ------------------------------------------------------------------ soundtrack (original, synthesised here)

def note(name: str) -> float:
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    return 440.0 * 2 ** ((names[name[0]] + 12 * (int(name[-1]) - 4)) / 12)


def env(n: int, attack: float, release: float) -> np.ndarray:
    tt = np.arange(n) / SR
    return np.clip(tt / attack, 0, 1) * np.clip((n / SR - tt) / release, 0, 1)


def lowpass(x: np.ndarray, hz: float) -> np.ndarray:
    return sosfilt(butter(2, hz, "low", fs=SR, output="sos"), x)


def soundtrack(scene_starts: list[float], total: float) -> np.ndarray:
    n = int((total + 0.5) * SR)
    t = np.arange(n) / SR
    mix = np.zeros(n)
    rng = np.random.default_rng(7)
    brand = scene_starts[3]  # brand reveal: the music lifts here

    # 1. dark drone under the story (A minor), swelling into the brand reveal
    drone = sum(np.sin(2 * np.pi * f * t + ph) for f, ph in [(55, 0), (82.4, 1), (110, 2), (164.8, 0.5)])
    drone *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t) ** 2
    mix += 0.05 * drone * np.clip((brand + 0.5 - t) / 1.5, 0, 1) * np.clip(t / 2, 0, 1)

    # 2. rain hiss in scene 1
    rain = lowpass(rng.standard_normal(n), 2500) * np.clip((scene_starts[1] - t) / 1.5, 0, 1) * np.clip(t / 1.5, 0, 1)
    mix += 0.035 * rain

    # 3. heartbeat thumps while the outbreak spreads (scenes 2-3)
    for beat in np.arange(scene_starts[1] + 0.6, brand - 0.4, 1.1):
        for k, dt in enumerate((0, 0.22)):
            i = int((beat + dt) * SR)
            m = int(0.35 * SR)
            if i + m < n:
                tt = np.arange(m) / SR
                mix[i:i + m] += (0.32 if k == 0 else 0.2) * np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)

    # 4. impact at the brand reveal
    i, m = int(brand * SR), int(2.5 * SR)
    tt = np.arange(m) / SR
    mix[i:i + m] += 0.6 * np.sin(2 * np.pi * (35 + 60 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 2.2)

    # 5. hopeful progression from the brand reveal: pads, arpeggio, soft kick and hats at 100 bpm
    beat = 60 / 100
    chords = [["A3", "C4", "E4"], ["F3", "A3", "C4"], ["C4", "E4", "G4"], ["G3", "B3", "D4"]]
    bar = 4 * beat
    k = 0
    for start in np.arange(brand, total, bar):
        ch = chords[k % 4]
        k += 1
        m = int(min(bar, total + 0.5 - start) * SR)
        i = int(start * SR)
        if m <= 0 or i >= n:
            break
        m = min(m, n - i)
        tt = np.arange(m) / SR
        pad = sum(np.sin(2 * np.pi * note(x) * tt) + 0.3 * np.sin(2 * np.pi * 2 * note(x) * tt) for x in ch)
        mix[i:i + m] += 0.045 * pad * env(m, 0.4, 0.5)
        bass = np.sin(2 * np.pi * note(ch[0]) / 2 * tt)
        mix[i:i + m] += 0.08 * bass * env(m, 0.05, 0.3)
        if start >= brand + 2 * bar - 0.01:  # rhythm enters after two bars
            for j in range(8):
                si = i + int(j * beat / 2 * SR)
                f = note(ch[j % 3]) * (2 if j % 2 else 1)
                pm = int(0.28 * SR)
                if si + pm < n:
                    pt = np.arange(pm) / SR
                    mix[si:si + pm] += 0.05 * np.sin(2 * np.pi * f * pt) * np.exp(-pt * 12)
                if j % 2 == 0 and si + int(0.2 * SR) < n:  # kick on the beat
                    km = int(0.2 * SR)
                    kt = np.arange(km) / SR
                    mix[si:si + km] += 0.22 * np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 40)) * kt) * np.exp(-kt * 18)
                else:  # hat off the beat
                    hm = int(0.05 * SR)
                    if si + hm < n:
                        mix[si:si + hm] += 0.025 * rng.standard_normal(hm) * np.exp(-np.arange(hm) / SR * 90)

    # 6. whoosh into every scene change
    for s in scene_starts[1:]:
        m = int(0.9 * SR)
        i = int(s * SR) - int(0.6 * SR)
        if i < 0 or i + m >= n:
            continue
        noise = rng.standard_normal(m)
        sweep = np.concatenate([lowpass(noise[c:c + 2205], 400 + 5000 * (c / m) ** 2) for c in range(0, m, 2205)])[:m]
        mix[i:i + m] += 0.12 * sweep * np.sin(np.pi * np.arange(m) / m) ** 2

    # master: gentle fade in/out, normalise
    mix *= np.clip(t / 0.8, 0, 1) * np.clip((total + 0.3 - t) / 3.0, 0, 1)
    mix = np.tanh(mix * 1.4)
    return (mix / np.abs(mix).max() * 0.85).astype(np.float32)


def main() -> None:
    durs = [int(d) for d in re.findall(r'class="scene[^"]*" data-dur="(\d+)"', FILM.read_text(encoding="utf-8"))]
    starts = list(np.cumsum([0] + durs[:-1]).astype(float))
    tmp = Path(tempfile.mkdtemp(prefix="epilag_film_"))
    try:
        frames, start, total = capture(tmp)
        print(f"captured {len(frames)} frames over {total} s ({len(frames) / total:.0f} fps average)")
        listing = to_video(frames, start, total, tmp)
        audio = soundtrack(starts, total)
        wavfile.write(tmp / "music.wav", SR, np.stack([audio, audio], axis=1))
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                        "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(tmp / "music.wav"),
                        "-r", str(FPS), "-vf", "scale=out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-tune", "animation", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                        str(OUT)], check=True)
        print("saved", OUT.relative_to(ROOT), f"{OUT.stat().st_size / 1e6:.1f} MB")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
