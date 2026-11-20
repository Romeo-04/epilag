# EpiLag-PH system flow: presenter script

Length **1:59.1**, 1920 x 1080, 30 fps · 274 words (read at the guide voice's pace).

The video follows **one forecast through the whole system**: Quezon City, the forecast made on 15 Sep 2024.
It goes from the data row to LightGBM, the alert, the dashboard and the game. It is built like a workflow diagram:
the graph stays on screen, a pulse carries the data from node to node, and a panel opens for each step.

**Two files** (in `docs/reel/flow/out/`):
- `epilag-flow-guide.mp4`: with the narration reading this script at the pace the video is cut to. Rehearse with it.
- `epilag-flow.mp4`: music and sound effects only. Record your voice over this one, or narrate it live.

Start each line when its scene starts: the step label at the top left changes, and the line's time is below.

| Time | Scene | Say | On screen | How |
|---|---|---|---|---|
| 0:01.0 | Title | **This is EpiLag-PH: how a dengue report becomes a forecast, a plan, and a game.** | Title card: EpiLag-PH, and the five stages of the flow. | Warm and slow. Let "a game" land. |
| 0:08.8 | The system | **Four public data sources go in, one LightGBM forecaster sits in the middle, and everything the health office sees comes out of it.** | The whole system draws itself: 4 data sources, the pipeline, 6 outputs. A pulse runs the full path. | Point left to right as you say it: in, middle, out. |
| 0:17.6 | Step 1 · Data | **Every week, for 104 areas, it builds one row: recent cases, the trend, last year's same week, twelve weeks of rain, heat, humidity, and the season.** | Inputs light up and fill Quezon City's row for the week ending 15 Sep 2024, item by item as you name them. | List rhythm. A small beat after "one row". |
| 0:29.1 | Step 2 · LightGBM | **LightGBM reads it with a quantile loss: a low, middle and high estimate, 2 to 8 weeks ahead. Conformal calibration widens the range to hold about 80 percent of outcomes.** | The 12-model grid lights row by row (low, middle, high) and column by column (2 to 8 weeks). The forecast fan: q10 152, q50 251, q90 360, then what happened (307). | Stress "low, middle and high". Slow down on "80 percent". |
| 0:41.4 | Step 3 · Alert | **Each forecast meets the area's own history. High end over the epidemic line: Watch. The middle over it: Outbreak warning.** | The four alert rules. Watch lights up with Quezon City's q90 of 360. A WATCH tag pops on the graph. | Pause before "Watch". It is the turning point. |
| 0:50.1 | Step 3 · Alert | **SHAP shows why: mostly recent cases, then rain and the season.** | SHAP bars grow: recent cases 68%, rain 18%, season 11%, population 3%. | Lighter, quicker: this is the reassurance. |
| 0:54.9 | Step 4 · Dashboard | **It all lands on the dashboard: what needs action now, the trend, and this week's to-do list.** | The live app's Overview: act-now strip, the trend, rising fastest, and "Do this week". | Name each thing as the camera reaches it. |
| 1:01.6 | Step 4 · Dashboard | **On the forecast map, click into NCR: above usual. Inside it, Quezon City is on Watch, about 1,754 cases in the next 8 weeks. Down to the barangay: Batasan Hills tops all 142.** | The 3D forecast map drills down: click NCR (Above usual, 1,113 expected), then Quezon City (Watch, 1,754 cases over 8 weeks, 142 barangays), then Batasan Hills (rank 1 of 142, 110 cases expected). | Three beats, one per click. Let each click land before the next. |
| 1:17.3 | Step 4 · Dashboard | **Every area gets a checklist, and a report card: for Quezon City, 7 of the last 8 weeks were right.** | Quezon City's page: Watch, 251, "What to do now", then the report card: 7 of 8 weeks right. | Stress "report card". |
| 1:24.1 | Step 4 · Dashboard | **Add a budget, and it ranks where clean-up and fogging prevent the most cases per peso, down to the barangay.** | Action plan with a ₱20M budget, then Quezon City's top barangays. | Stress "per peso". |
| 1:30.9 | Step 4 · Dashboard | **Every screen works in English or Filipino, and residents get a text message for phones without data.** | The dashboard flips from English to Filipino, then the residents' page with a one-SMS outlook (115 of 160 characters). | Say "Filipino" as the screen flips. |
| 1:37.3 | Step 5 · Dengue Drill | **The same forecasts power Dengue Drill: choose a model, play a real season, and the real cases keep score.** | Dengue Drill: the mission screen, the model choice, then a round on the 3D board. | More energy here; it is the fun part. |
| 1:44.8 | Close | **On Quezon City's 2024 season, it flagged Watch five weeks before the epidemic line. One pipeline, from data to decision. This is EpiLag-PH.** | End card: Watch on 15 Sep, line crossed 20 Oct, 5 weeks early; 622 · 30/32 · 104; logo, epilag.vercel.app and the GitHub repo. | Slow, final. Short pause before "EpiLag-PH". |


## Read-through version

**[0:01.0] Title**  
This is EpiLag-PH: how a dengue report becomes a forecast, a plan, and a game.

**[0:08.8] The system**  
Four public data sources go in, one LightGBM forecaster sits in the middle, and everything the health office sees comes out of it.

**[0:17.6] Step 1 · Data**  
Every week, for 104 areas, it builds one row: recent cases, the trend, last year's same week, twelve weeks of rain, heat, humidity, and the season.

**[0:29.1] Step 2 · LightGBM**  
LightGBM reads it with a quantile loss: a low, middle and high estimate, 2 to 8 weeks ahead. Conformal calibration widens the range to hold about 80 percent of outcomes.

**[0:41.4] Step 3 · Alert**  
Each forecast meets the area's own history. High end over the epidemic line: Watch. The middle over it: Outbreak warning.

**[0:50.1] Step 3 · Alert**  
SHAP shows why: mostly recent cases, then rain and the season.

**[0:54.9] Step 4 · Dashboard**  
It all lands on the dashboard: what needs action now, the trend, and this week's to-do list.

**[1:01.6] Step 4 · Dashboard**  
On the forecast map, click into NCR: above usual. Inside it, Quezon City is on Watch, about 1,754 cases in the next 8 weeks. Down to the barangay: Batasan Hills tops all 142.

**[1:17.3] Step 4 · Dashboard**  
Every area gets a checklist, and a report card: for Quezon City, 7 of the last 8 weeks were right.

**[1:24.1] Step 4 · Dashboard**  
Add a budget, and it ranks where clean-up and fogging prevent the most cases per peso, down to the barangay.

**[1:30.9] Step 4 · Dashboard**  
Every screen works in English or Filipino, and residents get a text message for phones without data.

**[1:37.3] Step 5 · Dengue Drill**  
The same forecasts power Dengue Drill: choose a model, play a real season, and the real cases keep score.

**[1:44.8] Close**  
On Quezon City's 2024 season, it flagged Watch five weeks before the epidemic line. One pipeline, from data to decision. This is EpiLag-PH.

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
