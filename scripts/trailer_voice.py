"""Synthesise the trailer's guide voice-over (docs/reel/trailer/vo/*.wav) and its word timings (docs/reel/trailer/vo.js).

The script of the trailer lives here, one line per beat; docs/reel/trailer/index.html places every cut, title card
and caption on these words. The voice is a Microsoft neural voice through edge-tts, as in scripts/reel_voice.py;
the team's own recording replaces it later (python scripts/reel_import_vo.py --trailer <folder>).

Usage: python scripts/trailer_voice.py [voice]     (default en-US-ChristopherNeural; try en-PH-JamesNeural, en-GB-RyanNeural)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel_voice  # noqa: E402

OUT = reel_voice.ROOT / "docs" / "reel" / "trailer"

LINES = [
    # cold open
    ("hook", "Quezon City. September 2024. The rains arrive. Water collects in old tires, gutters, flower pots. And in the dark, the mosquitoes start to breed."),
    ("bill", "The rain is free. The dengue bill comes later."),
    ("surge", "By February, 622 cases in a single week. Five times the epidemic line. 27 weeks above it."),
    ("late", "The health office saw it late, because cases are counted weeks after the rain that caused them."),
    ("brand", "What if they had seen it coming? This is EpiLag-PH."),
    ("rewind", "Rewind to September, and replay the season with only the data of the time. On September 15, five weeks before the line was crossed, Quezon City turns to Watch."),
    # the product
    ("see", "It forecasts dengue 2 to 8 weeks ahead, for 104 areas: every province, every region, and Quezon City."),
    ("act", "Open an area, and you get a plan, not just a number: what to do this week, and why it is flagged."),
    ("spend", "Give it a budget, and it ranks where clean-up and fogging prevent the most cases per peso, down to the barangay."),
    ("guide", "A guided tour on your first visit. In English, or in Filipino."),
    # the research
    ("test", "Then we tried to break it. 19 studies reviewed. Three rival methods, on the same test. Ours had the lowest error in 12 of 24 checks, and beat the simple rules in 5 of 6 test years."),
    ("losses", "It lost three times. We traced every loss to its cause, and published all of it."),
    # the game
    ("drill", "Don't take our word for it. Play Dengue Drill. 18 real seasons. Ten teams. Eight turns. Choose whose forecast you trust, and the real cases keep score."),
    # close
    ("close", "The rains will come again. This time, see dengue coming. EpiLag-PH."),
]

if __name__ == "__main__":
    reel_voice.OUT, reel_voice.LINES = OUT, LINES
    if len(sys.argv) < 2:
        reel_voice.VOICE = "en-US-ChristopherNeural"
    asyncio.run(reel_voice.main())
