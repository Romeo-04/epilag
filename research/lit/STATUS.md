# Person B status

- [x] **Step 1 is ready.** `feature_evidence.csv` has 27 rows: 12 current, 11 candidate, 4 proposed.
  - Every row has a mechanism, an expected lag and direction, and either a verified citation or `evidence_strength=none`.
  - The notes carry Person A's test results for the proposed rows. Minimum temperature and daily temperature range are marked untested.
- [x] `references.md`: 29 entries. makridakis2022, the Mandaue study and senson2026 are unverified, and none supports a claim.
- [x] Step 2: `rrl_matrix.csv` has 19 papers, 9 from the Philippines.
  - 16 are fully verified.
  - tuan2024 is verified with a caveat, rahman2025 from the abstract only, and johansson2019 partly.
- [x] Step 3: `research/analysis/causes.md`, made by `step3_checks.py` from Person A's extracts.
- [x] Step 4: `research/lit/positioning.md`.
- [x] Step 5: `causes.md`, step 5.
- [x] Step 6: `research/writeup/paper.md` (IMRADC), `slides.md` and `qa.md`.
- Steps 3–6 were committed and pushed to `research-b` (`ced441e`, `f9ccbf1`, `d62a1f7`). Person A reviewed them, and this revision applies that review. Only Kish's approval is pending.

## Person A's review (16 Nov): applied

**The 2023 margin question is answered.** The 2020–21 gap is not the cause (`research/results/STATUS.md`, "2023 calibration check").
- The calibration model, fit on regional data ending in 2019, forecast 2022 about 18% too low.
- The single margin then widened both ends of the 2023 range.

This replaces the earlier cause in:
- `causes.md`: finding 1b, the summary row, and the rerun line
- `paper.md`: Discussion, the calibration limitation, the Conclusion sentence on losses, and next step 2
- `qa.md`: the 2023 answer, and next step 2

**`paper.md` fixes**
- **Methods:**
  - three quantile models per lead time, each fit separately
  - how the margin is set
  - the definition of an outbreak start (2 or more weeks above the line), and the line's w−2 to w+2 window
  - the average of the four has no calibration of its own
  - Regions + QC live weather is rain only
- **Results:**
  - Provinces 2020 Watch: 19 of 23 caught (83%), 87% false alarms
  - negative binomial's win in Provinces 2019 at 2 weeks
  - ENSO for Regions + QC is mixed, not neutral
  - the live weather row is labelled as rain only
- **Discussion:**
  - 2020 is 79% lower nationally, and lower in every one of the 86 provinces
  - the 2023 margin is also compared with 2019's 0.176

**Other fixes**
- `slides.md`: the rain lag is now 5–7 weeks [sumi2017, carvajal2018], as in the paper.
- `qa.md`: the elevation answer now says "may", marked untested (hypothesis 3).

## Open

- **Untested:** why the 2018 and 2022 calibration models ran low. Person A's hypothesis is that their fit data were short or two years old.
- **Untested:** separate lower and upper margins [romano2019].
- **Site:** `site/` is Paul's, from the approved numbers.
- **Deck:** edited only after Kish approves.
