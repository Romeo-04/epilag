# Likely judge questions and short answers (draft)

Numbers and sources as in `research/writeup/paper.md`.

**Why LightGBM?**
- Dengue's drivers are non-linear: temperature risk peaks near 27.5 °C and falls after [seposo2023], and rain risk peaks at moderate amounts [iguchi2018].
- Boosted trees learn those shapes from the data, train fast [ke2017], and work with SHAP to explain each forecast.
- Tree models have done well for dengue in Metro Manila [carvajal2018].
- We tested it against three other methods on the same test. It had the lowest error in 12 of 24 checks; no other method had more than 7.

**Why not LSTM or another deep model?**
- Most areas have 3–7 training years. Deep sequence models usually need more data.
- In the national Philippine comparison, LSTM did not win; NNAR did [olana2025].
- We chose methods we can explain to a health officer.
- An LSTM is a fair next test. We haven't run one, so we don't claim LightGBM beats it.

**Why didn't topography help?**
- A nationwide Philippine study found elevation linked to infection rates, but not to reported cases [sy2026]. Our model forecasts reported cases.
- Elevation is fixed per area, and recent cases already tell the model each area's level.
- Added on its own, elevation helped slightly (7 of 8 checks, −1.9%). In the full model it added nothing, likely because temperature and humidity carry the same signal.

**What went wrong in 2023?**
- 2023 was the flattest year in the data, so "same as this week" was hard to beat. We lost by 4%: 58.0 against 55.6 cases.
- The range was too wide (92%, against an 80% target) because calibration used 2022. The regional data have no 2020–2021, so 2022 lacked last year's numbers and calibration overshot.
- Negative binomial did better that year. Combining methods is our next step.

**Why does "Watch" raise so many false alarms?**
- Watch fires when the high end of the range crosses the epidemic line. It is meant to be early and cheap: catch 79–100% of outbreak starts 4 weeks ahead, at the cost of 42–63% false alerts.
- Outbreak warning uses the middle forecast. It is stricter and catches fewer.

**Does weather actually matter?**
- For the regional model, yes, and more at longer leads. Weather's share of the model's attention goes from 11% at 2 weeks to 24% at 8 weeks, and heat, humidity and rain each help most at 6–8 weeks.
- That matches the literature's 4–18 week lags.
- At 2 weeks, recent cases already reflect past weather.
- For provinces, weather added nothing measurable in our test years.

**Why is the province skill against "same week last year" so high in 2020 (89%)?**
- The baseline copied the 2019 national epidemic into 2020, when reported cases fell 79% from late March. That number shows the baseline failing, not typical skill.
- Against "same as this week", 2020 skill was 20%.

**How do you know you didn't overfit?**
- Every test year is forecast by a model trained only on earlier years, and the epidemic lines use earlier years only.
- Four methods share the same test.
- We report the years we lost (2023, and 2-week 2019).

**What would you do next?**
1. Score the final variables on a new season.
2. Fix the calibration-year gap, and calibrate on more than one year.
3. Test an average of the methods that keeps Outbreak-warning catches.
4. Add weekly province data after 2021.

**Your research found better variables. Why not submit them?**
- Neighbours' cases (provinces) and heat and humidity (regions) beat the submitted model in 21 of 24 checks, median −1.4% (`research/results/STATUS.md`, "Final variables").
- They were chosen after seeing the test years, and no unseen year is left to score them on.
- So we report them as what the research found, and the submitted model as the main result. The next season is the real test.

**Why not use the average of the four methods, if it wins most often?**
- It had the lowest error in 11 of 24 checks and beat "same as this week" in all 24.
- But it caught fewer outbreak starts on Outbreak warning (30% against 36% for LightGBM).
- For an early-warning tool, missing outbreaks costs more than a small error gain (`research/results/STATUS.md`).

**Did adding temperature to the regional model fix 2023?**
- Partly. With heat and humidity added, the regional forecasts beat "same as this week" in 2023 at 2 and 4 weeks, which the submitted model did not.
