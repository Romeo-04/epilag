"""Synthesise the showreel voice-over (docs/reel/vo/*.wav) and its word timings (docs/reel/vo.js).

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
LINES = [
    ("rains", "Quezon City. September 2024. The rains arrive."),
    ("breed", "Standing water. Warm nights. In the dark, the mosquitoes breed."),
    ("surge", "By October, dengue crosses the epidemic line, and stays above it for 27 weeks, peaking at 622 cases in a single week."),
    ("late", "So why do we always act late? Because cases are counted weeks after the rain that caused them."),
    ("brand", "EpiLag-PH. See dengue coming. Act weeks earlier."),
    ("rewind", "Rewind to September. Trained only on earlier years, EpiLag-PH flagged Quezon City 5 weeks before it crossed the line, and kept it flagged all the way to the peak."),
    ("overview", "Here is the dashboard, replaying that season week by week. Watch the warnings build, weeks before the surge."),
    ("area", "For Quezon City, one clear call: Watch. And a checklist for this week, and the weeks after."),
    ("barangays", "Then, street level. The barangays to visit first: Batasan Hills, Payatas, Commonwealth."),
    ("drill", "And practice. Dengue Drill replays the real season, barangay by barangay: 5 million pesos, 8 turns, and the real cases keep score."),
    ("proof", "Tested honestly, on years it never saw. It beat simple rules in 5 of 6 tests, and caught most outbreak starts 4 weeks ahead."),
    ("close", "Hospitals see dengue a month late. EpiLag-PH sees it now."),
]
SAY = {"EpiLag-PH": "EpiLag P.H.", "2024": "twenty twenty-four"}


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
    # map the spoken words back onto the caption's words, so "P.H." shows as "EpiLag-PH"
    timed, k = [], 0
    for tok in text.split():
        n = len(spoken(tok).split())
        group = words[k:k + n] or words[-1:]
        k += n
        timed.append({"t": group[0]["t"], "d": round(group[-1]["t"] + group[-1]["d"] - group[0]["t"], 3), "w": tok})
    assert k == len(words), f"{key}: {k} caption words vs {len(words)} spoken"
    print(f"{key}: {len(x) / sr:.2f} s, {len(timed)} words")
    return {"id": key, "text": text, "dur": round(len(x) / sr, 3), "words": timed}


async def main() -> None:
    (OUT / "vo").mkdir(parents=True, exist_ok=True)
    lines = [await synth(k, t) for k, t in LINES]
    (OUT / "vo.js").write_text("window.VO = " + json.dumps({"voice": VOICE, "lines": lines}) + ";\n", encoding="utf-8")
    print("saved", (OUT / "vo.js").relative_to(ROOT), f"{sum(l['dur'] for l in lines):.1f} s of speech")


if __name__ == "__main__":
    asyncio.run(main())
