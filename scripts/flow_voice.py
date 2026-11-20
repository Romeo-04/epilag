"""Synthesise the system-flow video's guide voice (docs/reel/flow/vo/*.wav), its word timings (docs/reel/flow/vo.js)
and the presenter's script with timecodes (docs/reel/flow/SCRIPT.md).

The flow video (docs/reel/flow/index.html) follows one forecast through the whole system: Quezon City, the forecast
made on 15 Sep 2024. Every scene starts on its line and every highlight lands on a spoken word, so the guide voice
sets the pace. The voice is either the presenter's own recording of this script (scripts/own_voice.py: cut into the
lines, pauses shortened) or ElevenLabs (scripts/eleven_voice.py: a built-in voice on the v3 model with a light
Filipino accent, reading English; unchanged lines are reused from the cache).

Usage: python scripts/flow_voice.py --own <recording.m4a>     (the reel venv, for faster-whisper; FLOW_TEMPO=1.045 fits epilag 2.m4a in 2:00)
       ELEVENLABS_API_KEY=... python scripts/flow_voice.py      (ELEVEN_VOICE=<voice id> to change the voice)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eleven_voice  # noqa: E402

OUT = eleven_voice.OUT
GAP = 0.3  # silence after each line; the page uses the same value (docs/reel/flow/index.html, GAP)
LEAD = 1.0  # the title is on screen this long before the first word
PAD = {"intro": 0.25, "system": 0.2, "why": 0.15, "map": 0.15, "drill": 0.2}  # extra breath after these lines

# id, step label, what is said. Every number is from the repo: README.md, src/*.py, reports/*.csv,
# site/public/web/data (the Quezon City replay), and the app and game as captured in docs/reel/trailer/clips.
LINES = [
    ("intro", "", "This is EpiLag-PH: how a dengue report becomes a forecast, a plan, and a game."),
    ("system", "The system", "Four public data sources go in, one LightGBM forecaster sits in the middle, and everything the health office sees comes out of it."),
    ("data", "Step 1 · Data", "Every week, for 104 areas, it builds one row: recent cases, the trend, last year's same week, twelve weeks of rain, heat, humidity, and the season."),
    ("model", "Step 2 · LightGBM", "LightGBM reads it with a quantile loss: a low, middle and high estimate, 2 to 8 weeks ahead. Conformal calibration widens the range to hold about 80 percent of outcomes."),
    ("alert", "Step 3 · Alert", "Each forecast meets the area's own history. High end over the epidemic line: Watch. The middle over it: Outbreak warning."),
    ("why", "Step 3 · Alert", "SHAP shows why: mostly recent cases, then rain and the season."),
    ("dashboard", "Step 4 · Dashboard", "It all lands on the dashboard: what needs action now, the trend, and this week's to-do list."),
    ("map", "Step 4 · Dashboard", "On the forecast map, click into NCR: above usual. Inside it, Quezon City is on Watch, about 1,754 cases in the next 8 weeks. Down to the barangay: Batasan Hills tops all 142."),
    ("area", "Step 4 · Dashboard", "Every area gets a checklist, and a report card: for Quezon City, 7 of the last 8 weeks were right."),
    ("budget", "Step 4 · Dashboard", "Add a budget, and it ranks where clean-up and fogging prevent the most cases per peso, down to the barangay."),
    ("lang", "Step 4 · Dashboard", "Every screen works in English or Filipino, and residents get a text message for phones without data."),
    ("drill", "Step 5 · Dengue Drill", "The same forecasts power Dengue Drill: choose a model, play a real season, and the real cases keep score."),
    ("close", "", "On Quezon City's 2024 season, it flagged Watch five weeks before the epidemic line. One pipeline, from data to decision. This is EpiLag-PH."),
]
eleven_voice.SAY.update({"EpiLag-PH": "EpiLag P.H.", "LightGBM": "Light G.B.M.", "SHAP": "Shap", "104": "a hundred and four",
                         "NCR": "N.C.R.", "2024": "twenty twenty-four", "1,754": "seventeen hundred fifty-four"})


def timecode(s: float) -> str:
    return f"{int(s // 60)}:{s % 60:04.1f}"


# what the screen shows during each line, and how to say it (for the presenter's script)
ON_SCREEN = {
    "intro": ("Title card: EpiLag-PH, and the five stages of the flow.", "Warm and slow. Let \"a game\" land."),
    "system": ("The whole system draws itself: 4 data sources, the pipeline, 6 outputs. A pulse runs the full path.", "Point left to right as you say it: in, middle, out."),
    "data": ("Inputs light up and fill Quezon City's row for the week ending 15 Sep 2024, item by item as you name them.", "List rhythm. A small beat after \"one row\"."),
    "model": ("The 12-model grid lights row by row (low, middle, high) and column by column (2 to 8 weeks). The forecast fan: q10 152, q50 251, q90 360, then what happened (307).", "Stress \"low, middle and high\". Slow down on \"80 percent\"."),
    "alert": ("The four alert rules. Watch lights up with Quezon City's q90 of 360. A WATCH tag pops on the graph.", "Pause before \"Watch\". It is the turning point."),
    "why": ("SHAP bars grow: recent cases 68%, rain 18%, season 11%, population 3%.", "Lighter, quicker: this is the reassurance."),
    "dashboard": ("The live app's Overview: act-now strip, the trend, rising fastest, and \"Do this week\".", "Name each thing as the camera reaches it."),
    "map": ("The 3D forecast map drills down: click NCR (Above usual, 1,113 expected), then Quezon City (Watch, 1,754 cases over 8 weeks, 142 barangays), then Batasan Hills (rank 1 of 142, 110 cases expected).", "Three beats, one per click. Let each click land before the next."),
    "area": ("Quezon City's page: Watch, 251, \"What to do now\", then the report card: 7 of 8 weeks right.", "Stress \"report card\"."),
    "budget": ("Action plan with a ₱20M budget, then Quezon City's top barangays.", "Stress \"per peso\"."),
    "lang": ("The dashboard flips from English to Filipino, then the residents' page with a one-SMS outlook (115 of 160 characters).", "Say \"Filipino\" as the screen flips."),
    "drill": ("Dengue Drill: the mission screen, the model choice, then a round on the 3D board.", "More energy here; it is the fun part."),
    "close": ("End card: Watch on 15 Sep, line crossed 20 Oct, 5 weeks early; 622 · 30/32 · 104; logo, epilag.vercel.app and the GitHub repo.", "Slow, final. Short pause before \"EpiLag-PH\"."),
}


def script_md(lines: list[dict]) -> str:
    t, rows, plain = LEAD, [], []
    for (key, step, _), line in zip(LINES, lines):
        scene = step or ("Title" if key == "intro" else "Close")
        shows, how = ON_SCREEN[key]
        rows.append(f"| {timecode(t)} | {scene} | **{line['text']}** | {shows} | {how} |")
        plain.append(f"**[{timecode(t)}] {scene}**  \n{line['text']}")
        t += line["dur"] + GAP + PAD.get(key, 0)
    total = t + 3.2  # the end card holds after the last line (index.html, END_HOLD)
    words = sum(len(l["text"].split()) for l in lines)
    head = f"""# EpiLag-PH system flow: presenter script

Length **{timecode(total)}**, 1920 x 1080, 30 fps · {words} words (read at the guide voice's pace).

The video follows **one forecast through the whole system**: Quezon City, the forecast made on 15 Sep 2024.
It goes from the data row to LightGBM, the alert, the dashboard and the game. It is built like a workflow diagram:
the graph stays on screen, a pulse carries the data from node to node, and a panel opens for each step.

**Two files** (in `docs/reel/flow/out/`):
- `epilag-flow-guide.mp4`: with the narration reading this script at the pace the video is cut to. Rehearse with it.
- `epilag-flow.mp4`: music and sound effects only. Record your voice over this one, or narrate it live.

Start each line when its scene starts: the step label at the top left changes, and the line's time is below.

| Time | Scene | Say | On screen | How |
|---|---|---|---|---|
"""
    read = "\n\n## Read-through version\n\n" + "\n\n".join(plain) + "\n"
    return head + "\n".join(rows) + "\n" + read + FACTS


FACTS = """
## What is on screen, and where it comes from

| On screen | Source |
|---|---|
| 4 sources: DOH dengue reports (HDX), UPRI-NOAH weekly cases, ERA5 weather (Open-Meteo), PSA population (OCHA) | README.md, Data |
| 104 areas = 86 provinces + 17 regions + Quezon City | README.md, Method |
| The row: cases in the last 4 weeks, 4- and 12-week averages, trend, same week last year, rain for each of the last 12 weeks, 4/8/12-week totals, heavy-rain days, humidity and temperature lags, season, population | src/features.py |
| Quezon City, week ending 15 Sep 2024: 297, 216, 207, 232 cases (this week back to 3 weeks ago); 111 in the same week of 2023; population 2,960,048 | site/public/web/data/region_qc_history.json, meta.json |
| LightGBM quantile regression, q10 / q50 / q90, one model set per horizon (2, 4, 6, 8 weeks): 12 models; 400 trees, learning rate 0.03, 31 leaves | src/backtest.py, src/features.py |
| Conformalized quantile regression, widened to cover 80% on the last training year | src/backtest.py, conformal_margin |
| Forecast made 15 Sep 2024 for 13 Oct (4 weeks ahead): 251, likely 152–360; what happened: 307 | region_qc_backtest.json (trained on years before 2024 only) |
| Alert rules: q50 over the epidemic line = Outbreak warning, q90 over it = Watch, q50 over the usual level = Above usual; usual = mean, epidemic = mean + 2 SD, same weeks ±2, earlier years | src/train_final.py, README.md |
| SHAP at 4 weeks, regions + Quezon City: recent cases 68%, rain (12 weekly lags) 18%, season 11%, population 3% | reports/shap_region_qc.csv |
| NCR: Above usual, 1,113 expected; Quezon City: Watch, 1,754 cases over the next 8 weeks, 142 barangays; Batasan Hills: rank 1 of 142, 110 expected over 8 weeks | the app's forecast map, replaying 15 Sep 2024 (site/public/web/data) |
| Quezon City report card: 7 of the last 8 weeks right (forecast made 4 weeks before) | the app's Area detail, replaying 15 Sep 2024 |
| SMS: "DENGUE WATCH Quezon City: ..." 115/160 characters | the app's For residents page |
| The app and the game | real screen captures, docs/reel/flow/clips |
| Watch from 15 Sep 2024; the line was crossed in the week ending 20 Oct (5 weeks later); 27 weeks above it; peak 622 | README.md |
| 30 of 32 provinces flagged 4 weeks ahead in the 2019 replay | README.md |
"""


def main() -> None:
    (OUT / "vo").mkdir(parents=True, exist_ok=True)
    voice, name = eleven_voice, f"ElevenLabs {eleven_voice.MODEL} {eleven_voice.VOICE}"
    if sys.argv[1:2] == ["--own"]:
        import own_voice
        own_voice.prepare(Path(sys.argv[2]).expanduser(), [(k, text) for k, _, text in LINES])
        voice, name = own_voice, f"own recording ({Path(sys.argv[2]).name}, tempo {own_voice.TEMPO})"
    lines = [voice.synth(k, text) for k, _, text in LINES]
    for line, (key, step, _) in zip(lines, LINES):
        line["step"], line["pad"] = step, PAD.get(key, 0)
    payload = {"voice": name, "gap": GAP, "lead": LEAD, "lines": lines}
    (OUT / "vo.js").write_text("window.VO = " + json.dumps(payload) + ";\n", encoding="utf-8")
    (OUT / "SCRIPT.md").write_text(script_md(lines), encoding="utf-8")
    speech = sum(l["dur"] for l in lines)
    print(f"saved docs/reel/flow/vo.js and SCRIPT.md · {speech:.1f} s of speech")


if __name__ == "__main__":
    main()
