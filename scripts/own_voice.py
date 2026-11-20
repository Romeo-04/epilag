"""The presenter's own recording as the flow video's voice: cut into the script's lines, with word timings.

Same return format as scripts/eleven_voice.py's synth(), so scripts/flow_voice.py can use either. The recording is
read once with faster-whisper (word timestamps), cached in docs/reel/flow/vo/own.json. Each script line is found in
it, cut at the quietest point between lines, its long pauses shortened to MAX_PAUSE, levelled to -16 LUFS and saved
as docs/reel/flow/vo/<id>.wav. TEMPO (env FLOW_TEMPO, default 1) speeds the whole voice up without changing its
pitch, to fit the video under a length.

Needs faster-whisper the first time (the reel venv: ~/.venvs/reel/bin/python).
"""
import difflib
import json
import os
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile

OUT = Path(__file__).resolve().parents[1] / "docs" / "reel" / "flow"
SR = 44100
MAX_PAUSE = float(os.environ.get("FLOW_MAX_PAUSE", 0.25))  # longest pause kept inside a line, seconds
TEMPO = float(os.environ.get("FLOW_TEMPO", 1.0))
PROMPT = "EpiLag-PH, LightGBM, SHAP, NCR, Quezon City, Batasan Hills, Dengue Drill, barangay"
NUM = {"two": "2", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "twelve": "12"}
FF = imageio_ffmpeg.get_ffmpeg_exe()
RECORDING: Path | None = None
_cache: dict = {}


def norm(w: str) -> str:
    w = "".join(ch for ch in w.lower() if ch.isalnum())
    return NUM.get(w, w)


def transcript(rec: Path) -> list[dict]:
    f = OUT / "vo" / "own.json"
    key = {"file": rec.name, "size": rec.stat().st_size}
    if f.exists():
        old = json.loads(f.read_text())
        if old.get("key") == key:
            return old["words"]
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel("small.en", compute_type="int8").transcribe(str(rec), word_timestamps=True, language="en", initial_prompt=PROMPT)
    words = [{"t": round(w.start, 3), "e": round(w.end, 3), "w": w.word.strip()} for s in segs for w in s.words]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"key": key, "words": words}))
    return words


def load(rec: Path) -> np.ndarray:
    """The recording as 44.1 kHz mono float, levelled to -16 LUFS."""
    raw = subprocess.run([FF, "-loglevel", "error", "-i", str(rec), "-ac", "1", "-ar", str(SR),
                          "-af", "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def quietest(x: np.ndarray, t0: float, t1: float) -> float:
    """The quietest 20 ms between two times (where to cut between lines)."""
    a, b = int(t0 * SR), int(t1 * SR)
    if b - a < 900:
        return (t0 + t1) / 2
    n = 882
    e = [float(np.sqrt(np.mean(x[i:i + n] ** 2))) for i in range(a, b - n, 220)]
    return (a + 220 * int(np.argmin(e)) + n / 2) / SR


def squeeze(x: np.ndarray) -> tuple[np.ndarray, list[tuple[float, float]]]:
    """Shorten every pause longer than MAX_PAUSE; returns the audio and a map of (old time, new time) points."""
    n = 441  # 10 ms
    env = np.array([np.sqrt(np.mean(x[i:i + n] ** 2)) for i in range(0, len(x), n)])
    quiet = env < 10 ** (-42 / 20)
    keep, pts, i, out_t = [], [(0.0, 0.0)], 0, 0.0
    runs, start = [], None
    for k, q in enumerate(list(quiet) + [False]):
        if q and start is None:
            start = k
        elif not q and start is not None:
            runs.append((start, k))
            start = None
    cur = 0
    for a, b in runs:
        if (b - a) * n / SR <= MAX_PAUSE or a == 0 or b >= len(quiet):
            continue
        cut0 = (a * n) + int(MAX_PAUSE / 2 * SR)
        cut1 = (b * n) - int(MAX_PAUSE / 2 * SR)
        keep.append(x[cur:cut0])
        out_t += (cut0 - cur) / SR
        pts += [(cut0 / SR, out_t), (cut1 / SR, out_t)]
        cur = cut1
    keep.append(x[cur:])
    out_t += (len(x) - cur) / SR
    pts.append((len(x) / SR, out_t))
    return np.concatenate(keep), pts


def remap(t: float, pts: list[tuple[float, float]]) -> float:
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        if t <= a1:
            return b0 if a1 == a0 else b0 + (t - a0) * (b1 - b0) / (a1 - a0)
    return pts[-1][1]


def tempo(x: np.ndarray) -> np.ndarray:
    if abs(TEMPO - 1) < 1e-3:
        return x
    r = subprocess.run([FF, "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={TEMPO}",
                        "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(r, np.float32).copy()


def split(lines: list[tuple[str, str]]) -> dict:
    """Find every line in the recording and cut it out."""
    words = transcript(RECORDING)
    x = load(RECORDING)
    cap, owner = [], []
    for li, (_, text) in enumerate(lines):
        for tok in text.split():
            cap.append(norm(tok))
            owner.append(li)
    said = [norm(w["w"]) for w in words]
    line_of = [None] * len(words)
    for blk in difflib.SequenceMatcher(None, cap, said, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            line_of[blk.b + j] = owner[blk.a + j]
    first = {li: min(k for k, o in enumerate(line_of) if o == li) for li in range(len(lines))}
    last = {li: max(k for k, o in enumerate(line_of) if o == li) for li in range(len(lines))}
    # words between one line's last match and the next line's first match go to the line across the longest pause
    bounds = []
    for li in range(len(lines) - 1):
        a, b = last[li], first[li + 1]
        gaps = [(words[k + 1]["t"] - words[k]["e"], k) for k in range(a, b)]
        k = max(gaps)[1]
        bounds.append((k, quietest(x, words[k]["e"], words[k + 1]["t"])))
    out = {}
    for li, (name, text) in enumerate(lines):
        w0 = bounds[li - 1][0] + 1 if li else 0
        w1 = bounds[li][0] if li < len(lines) - 1 else len(words) - 1
        t0 = max(bounds[li - 1][1] if li else 0.0, words[w0]["t"] - 0.08)
        t1 = min(bounds[li][1] if li < len(lines) - 1 else len(x) / SR, words[w1]["e"] + 0.15)
        seg, pts = squeeze(x[int(t0 * SR):int(t1 * SR)])
        seg = tempo(seg)
        raw = [{"t": round(remap(w["t"] - t0, pts) / TEMPO, 3),
                "d": round(max(0.05, (remap(w["e"] - t0, pts) - remap(w["t"] - t0, pts)) / TEMPO), 3), "w": w["w"]}
               for w in words[w0:w1 + 1]]
        fade = int(0.01 * SR)
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        wavfile.write(OUT / "vo" / f"{name}.wav", SR, (np.clip(seg, -1, 1) * 32767).astype(np.int16))
        out[name] = {"id": name, "dur": round(len(seg) / SR, 3), "raw": raw}
        print(f"{name}: {out[name]['dur']:.2f} s  «{' '.join(w['w'] for w in words[w0:w1 + 1])}»")
    return out


def align(text: str, words: list[dict]) -> list[dict]:
    """Put the caption's own words on the spoken words' times."""
    toks = text.split()
    cap, said = [norm(t) for t in toks], [norm(w["w"]) for w in words]
    at = [None] * len(toks)
    for blk in difflib.SequenceMatcher(None, cap, said, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            at[blk.a + j] = blk.b + j
    timed = []
    for i, tok in enumerate(toks):
        if at[i] is not None:
            w = words[at[i]]
            timed.append({"t": w["t"], "d": w["d"], "w": tok})
        else:
            prev = timed[-1] if timed else None
            nxt = next((words[at[k]] for k in range(i + 1, len(toks)) if at[k] is not None), None)
            t0 = prev["t"] + prev["d"] if prev else 0.0
            t1 = nxt["t"] if nxt else t0 + 0.4
            timed.append({"t": round(t0, 3), "d": round(max(0.1, t1 - t0), 3), "w": tok})
    return timed


def prepare(rec: Path, lines: list[tuple[str, str]]) -> None:
    global RECORDING
    RECORDING = rec
    (OUT / "vo").mkdir(parents=True, exist_ok=True)
    _cache.update(split(lines))


def synth(name: str, text: str) -> dict:
    c = _cache[name]
    return {"id": name, "text": text, "dur": c["dur"], "words": align(text, c["raw"])}
