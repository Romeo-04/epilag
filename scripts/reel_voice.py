"""Synthesise a guide voice-over for the demo video (the team records the real one) (docs/reel/vo/*.wav) and its word timings (docs/reel/vo.js).

One line per scene. Each line is spoken by a Microsoft neural voice through edge-tts (pip install edge-tts;
it needs the internet), decoded to 44.1 kHz mono WAV with ffmpeg, and timed word by word, so the reel's
captions land on the words as they are said.

Usage: python scripts/reel_voice.py [voice]     (default en-US-AndrewMultilingualNeural; try en-PH-JamesNeural)
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reel"
VOICE = sys.argv[1] if len(sys.argv) > 1 else "en-US-AndrewMultilingualNeural"
RATE, PITCH = "-4%", "-3Hz"

# id, caption (what the screen shows); the voice reads the same words with SAY applied
LINES = [  # as recorded by the team (captions show these words)
    ("rains", "Quezon City. September 2024. The rains arrive. Water collects in old tires, gutters, flower pots, and in the dark, the mosquitoes start to breed."),
    ("report", "At the city health office, the dengue report looks quiet. A few cases, like every September. But those numbers are already old. Cases are counted after people get sick, weeks after the rain that caused them."),
    ("surge", "By late October, dengue crosses the epidemic line, and stays above it for 27 weeks. In February, 622 cases in a single week. Five times the line. The clean-up drives and fogging came, but only after the wards were full."),
    ("question", "What if the health office could have seen it coming? This is EpiLag-PH."),
    ("rewind", "Let's rewind to September, and replay the season with the forecasts EpiLag-PH would have made that week, using only the data available at that time. On September 15, five weeks before the line was crossed, Quezon City turns to Watch."),
    ("dashboard", "The dashboard shows which areas need action now. On the 3D map, columns rise with the alert level. Every forecast looks 2–8 weeks ahead, with a likely range, for every region and Quezon City."),
    ("area", "Open Quezon City, and the health office gets a plan, not just a number: what to do today, in weeks 1–2, and weeks 2–4, and why it is flagged: recent cases, the season, rain, heat and humidity."),
    ("budget", "Give it a budget, and it ranks where clean-up and fogging prevent the most cases per peso. It names the barangays to visit first."),
    ("hood", "LightGBM quantile models, one for each forecast horizon, ranges calibrated with conformal prediction, and SHAP values that explain every forecast."),
    ("proof", "We tested it only on years it had never seen. In a replay of 2019, 30 of the 32 provinces that later crossed the epidemic line were flagged four weeks ahead. It has limits. Watch alerts raise false alarms, and it called the outbreak, not its exact height."),
    ("drill", "To feel what five weeks are worth, play Dengue Drill, and run the response yourself, barangay by barangay. In tests, following EpiLag-PH prevented more cases in 11 of 17 regions."),
    ("close", "Back to September. The rains still come. But this time, the health office sees dengue coming, five weeks early. This is EpiLag-PH."),
]
SAY = {"EpiLag-PH": "EpiLag P.H.", "2024": "twenty twenty-four", "3D": "three-D"}


def spoken(text: str) -> str:
    for a, b in SAY.items():
        text = text.replace(a, b)
    return text


async def synth(key: str, text: str) -> dict:
    mp3, words = OUT / "vo" / f"{key}.mp3", []
    com = edge_tts.Communicate(spoken(text), VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"t": round(chunk["offset"] / 1e7, 3), "d": round(chunk["duration"] / 1e7, 3), "w": chunk["text"]})
    wav = mp3.with_suffix(".wav")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)], check=True)
    mp3.unlink()
    sr, x = wavfile.read(wav)
    # map the spoken words back onto the caption's words, so "P.H." shows as "EpiLag-PH". The voice's word
    # boundaries don't always split the same way (numbers, contractions), so align them by text and interpolate gaps.
    import difflib
    norm = lambda w: "".join(ch for ch in w.lower() if ch.isalnum())
    toks = text.split()
    cap = [norm(spoken(t).split()[0]) for t in toks]
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
            prev = next((timed[k] for k in range(i - 1, -1, -1)), None)
            nxt = next((words[at[k]] for k in range(i + 1, len(toks)) if at[k] is not None), None)
            t0 = prev["t"] + prev["d"] if prev else 0.0
            t1 = nxt["t"] if nxt else t0 + 0.4
            timed.append({"t": round(t0, 3), "d": round(max(0.1, t1 - t0), 3), "w": tok})
    print(f"{key}: {len(x) / sr:.2f} s, {len(timed)} words")
    return {"id": key, "text": text, "dur": round(len(x) / sr, 3), "words": timed}


async def main() -> None:
    (OUT / "vo").mkdir(parents=True, exist_ok=True)
    lines = [await synth(k, t) for k, t in LINES]
    (OUT / "vo.js").write_text("window.VO = " + json.dumps({"voice": VOICE, "lines": lines}) + ";\n", encoding="utf-8")
    print("saved", (OUT / "vo.js").relative_to(ROOT), f"{sum(l['dur'] for l in lines):.1f} s of speech")


if __name__ == "__main__":
    asyncio.run(main())
