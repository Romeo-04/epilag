"""ElevenLabs text-to-speech for the flow video's guide voice: one line in, a 44.1 kHz mono WAV and word timings out.

Same return format as scripts/reel_voice.py's synth(), so scripts/flow_voice.py can use either. The voice is one of
ElevenLabs' built-in voices on the v3 model, asked for a light Filipino accent with an audio tag (free accounts
can't use the shared Filipino voices through the API). Word timings come from the /with-timestamps endpoint
(character alignment, grouped into words).

Each line is cached in docs/reel/flow/vo/<id>.json with the text, voice and settings it was made from, so a re-run
only spends characters on lines that changed. Needs ELEVENLABS_API_KEY (or ELEVENLABS_API_KEY_FILE) in the
environment and the internet.
"""
import base64
import difflib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import imageio_ffmpeg
from scipy.io import wavfile

VOICE = os.environ.get("ELEVEN_VOICE", "iP95p4xoKVk53GoZ742B")  # Chris: charming, down-to-earth (premade)
MODEL = os.environ.get("ELEVEN_MODEL", "eleven_v3")
TAG = "[Filipino accent] "
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75}
SAY: dict[str, str] = {}
OUT = Path(__file__).resolve().parents[1] / "docs" / "reel" / "flow"


def key() -> str:
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    f = os.environ.get("ELEVENLABS_API_KEY_FILE")
    if f:
        return Path(f).read_text().strip()
    raise SystemExit("set ELEVENLABS_API_KEY (or ELEVENLABS_API_KEY_FILE)")


def spoken(text: str) -> str:
    for a, b in SAY.items():
        text = text.replace(a, b)
    return text


def request(text: str) -> dict:
    body = json.dumps({"text": text, "model_id": MODEL, "voice_settings": SETTINGS}).encode()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128"
    for k in range(4):
        req = urllib.request.Request(url, body, {"xi-api-key": key(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503) and k < 3:
                time.sleep(3 + 3 * k)
                continue
            raise SystemExit(f"ElevenLabs {e.code}: {msg}")
    raise SystemExit("ElevenLabs: no audio")


def words_from(al: dict, skip: int) -> list[dict]:
    """Group the character alignment into words, skipping the first `skip` characters (the accent tag)."""
    chars, t0s, t1s = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur = [], None
    for i in range(skip, len(chars)):
        c = chars[i]
        if c.isspace():
            cur = None
            continue
        if cur is None:
            cur = {"t": t0s[i], "e": t1s[i], "w": ""}
            out.append(cur)
        cur["w"] += c
        cur["e"] = t1s[i]
    return [{"t": round(w["t"], 3), "d": round(max(0.05, w["e"] - w["t"]), 3), "w": w["w"]} for w in out]


def align(text: str, words: list[dict]) -> list[dict]:
    """Put the caption's own words on the spoken words' times (as scripts/reel_voice.py does)."""
    norm = lambda w: "".join(ch for ch in w.lower() if ch.isalnum())
    toks = text.split()
    cap = [norm(spoken(t).split()[0]) if spoken(t).split() else norm(t) for t in toks]
    said = [norm(w["w"]) for w in words]
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


def synth(name: str, text: str) -> dict:
    vo = OUT / "vo"
    vo.mkdir(parents=True, exist_ok=True)
    said = TAG + spoken(text)
    meta = {"said": said, "voice": VOICE, "model": MODEL, "settings": SETTINGS}
    cache, wav = vo / f"{name}.json", vo / f"{name}.wav"
    if cache.exists() and wav.exists():
        old = json.loads(cache.read_text())
        if old.get("meta") == meta:
            print(f"{name}: cached")
            return old["line"] | {"text": text, "words": align(text, old["raw"])}
    r = request(said)
    mp3 = vo / f"{name}.mp3"
    mp3.write_bytes(base64.b64decode(r["audio_base64"]))
    # trim the silence ElevenLabs leaves at the end, keep 0.12 s of tail
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1", "-ar", "44100",
                    "-af", "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.12,areverse", str(wav)], check=True)
    mp3.unlink()
    sr, x = wavfile.read(wav)
    raw = words_from(r.get("alignment") or r["normalized_alignment"], len(TAG))
    line = {"id": name, "text": text, "dur": round(len(x) / sr, 3)}
    cache.write_text(json.dumps({"meta": meta, "line": line, "raw": raw}))
    print(f"{name}: {line['dur']:.2f} s, {len(raw)} words, {len(said)} characters")
    return line | {"words": align(text, raw)}
