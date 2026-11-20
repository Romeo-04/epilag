"""Bring the team's recorded voice-over into the demo video (docs/reel/vo/*.wav and docs/reel/vo.js).

Reads one recording per scene, 01 to 12 (any format ffmpeg reads: m4a, mp3, wav...), from a folder:
trims the silence at both ends, evens out the loudness, and finds when each word is said (faster-whisper),
so the captions and every cut in docs/reel/index.html land on the recorded words.
The caption text stays the script's text (LINES in scripts/reel_voice.py); only the timings come from the audio.

Usage: python scripts/reel_import_vo.py [folder]     (default ~/epilag-submission/vo)
Then:  python scripts/record_reel.py --out demo.mp4

For the trailer (docs/reel/trailer, 13 lines, recordings 01 to 13 in the order of scripts/trailer_voice.py):
       python scripts/reel_import_vo.py --trailer [folder]     (default ~/epilag-submission/vo-trailer)
Then:  python scripts/record_trailer.py
"""
import difflib
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
TRAILER = "--trailer" in sys.argv  # the trailer's 13 lines (scripts/trailer_voice.py) instead of the demo's 12
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
if TRAILER:
    from trailer_voice import LINES  # noqa: E402
else:
    from reel_voice import LINES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reel" / ("trailer" if TRAILER else "")
SRC = Path(ARGS[0]).expanduser() if ARGS else Path.home() / "epilag-submission" / ("vo-trailer" if TRAILER else "vo")
SR = 44100


def load(path: Path) -> np.ndarray:
    wav = OUT / "vo" / "_tmp.wav"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                    "-af", "highpass=f=70,afftdn=nf=-25,lowpass=f=12000", str(wav)], check=True)
    _, x = wavfile.read(wav)
    wav.unlink()
    return x.astype(np.float64) / 32768.0


def trim(x: np.ndarray, pad: float = 0.12) -> np.ndarray:
    """Cut the silence before the first word and after the last, keeping a short breath of room tone."""
    win = int(0.02 * SR)
    frames = np.abs(x[: len(x) // win * win]).reshape(-1, win).max(axis=1)
    loud = np.where(frames > max(0.02, frames.max() * 0.08, np.percentile(frames, 15) * 1.8))[0]
    if not len(loud):
        return x
    a = max(0, loud[0] * win - int(pad * SR))
    b = min(len(x), (loud[-1] + 1) * win + int(pad * SR))
    return x[a:b]


def tighten(x: np.ndarray, longest: float = 0.7, keep: float = 0.45) -> np.ndarray:
    """Shorten pauses inside a take: any silence longer than `longest` seconds is cut down to `keep`."""
    win = int(0.02 * SR)
    n = len(x) // win
    fr = np.abs(x[: n * win]).reshape(-1, win).max(axis=1)
    loud = fr > max(0.02, fr.max() * 0.06, np.percentile(fr, 15) * 1.8)
    out, i = [], 0
    while i < n:
        j = i
        while j < n and loud[j] == loud[i]:
            j += 1
        seg = x[i * win:j * win]
        if not loud[i] and (j - i) * win > longest * SR:
            h = int(keep * SR / 2)
            seg = np.concatenate([seg[:h], seg[-h:]])
        out.append(seg)
        i = j
    out.append(x[n * win:])
    return np.concatenate(out)


def normalise(x: np.ndarray, peak: float = 0.89) -> np.ndarray:
    return x / max(1e-6, np.abs(x).max()) * peak


def words_of(model, wav: Path) -> list:
    segs, _ = model.transcribe(str(wav), language="en", word_timestamps=True, beam_size=5)
    return [{"t": round(w.start, 3), "d": round(w.end - w.start, 3), "w": w.word.strip()} for s in segs for w in s.words]


def align(text: str, said: list) -> list:
    """The script's words, each timed by the recorded word it matches (gaps are interpolated)."""
    norm = lambda w: "".join(ch for ch in w.lower() if ch.isalnum())
    toks = text.split()
    cap, got = [norm(t) for t in toks], [norm(w["w"]) for w in said]
    at = [None] * len(toks)
    for blk in difflib.SequenceMatcher(None, cap, got, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            at[blk.a + j] = blk.b + j
    timed = []
    for i, tok in enumerate(toks):
        if at[i] is not None:
            w = said[at[i]]
            timed.append({"t": w["t"], "d": w["d"], "w": tok})
        else:
            prev = timed[-1] if timed else None
            nxt = next((said[at[k]] for k in range(i + 1, len(toks)) if at[k] is not None), None)
            t0 = prev["t"] + prev["d"] if prev else 0.0
            t1 = nxt["t"] if nxt else t0 + 0.4
            timed.append({"t": round(t0, 3), "d": round(max(0.1, t1 - t0), 3), "w": tok})
    return timed, sum(a is not None for a in at)


def main() -> None:
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    (OUT / "vo").mkdir(parents=True, exist_ok=True)
    lines, total = [], 0.0
    for i, (key, text) in enumerate(LINES, start=1):
        found = sorted(p for p in SRC.glob(f"{i:02d}.*") if not p.name.startswith("."))
        if not found:
            raise SystemExit(f"missing recording {i:02d}.* in {SRC} (scene: {key})")
        x = normalise(tighten(trim(load(found[0]))))
        wav = OUT / "vo" / f"{key}.wav"
        wavfile.write(wav, SR, (x * 32767).astype(np.int16))
        timed, hit = align(text, words_of(model, wav))
        dur = len(x) / SR
        total += dur
        flag = "" if hit >= 0.7 * len(timed) else "   <- check this take: few words matched the script"
        print(f"{i:02d} {key:10s} {dur:5.1f} s   {hit}/{len(timed)} words matched{flag}")
        lines.append({"id": key, "text": text, "dur": round(dur, 3), "words": timed})
    (OUT / "vo.js").write_text("window.VO = " + json.dumps({"voice": "team recording", "lines": lines}) + ";\n", encoding="utf-8")
    print(f"saved {(OUT / 'vo.js').relative_to(ROOT)}: {total:.1f} s of speech (the film adds about 13 s; keep it under 2:50)")


if __name__ == "__main__":
    main()
