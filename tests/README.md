# Tests (`tests/`)

```bash
pytest tests                       # everything
pytest tests/test_allocate.py      # one file
```

The browser tests serve the built site from `docs/` and drive it with Playwright, so build first. Without
Playwright they are skipped, not failed.

```bash
python scripts/build_web.py
cd site && npm ci && npm run build && cd ..
playwright install chromium     # Playwright itself is in requirements.txt
```

| File | What it checks | Needs the built site |
| --- | --- | --- |
| `test_allocate.py` | The budget plan (`src/allocate.py`): sums 8 weeks of forecast, funds the best value per peso first, stays within the budget and coverage limits, orders the low/central/high ranges, and gives an empty plan for a zero budget | No |
| `test_web_logic.py` | The JavaScript app computes what the Python does, on the same data: alert levels, thresholds, replays, the "30 of 32" claim, budget plans, each area's alert track record | Yes |
| `test_drill_rules.py` | Dengue Drill's rules (`site/src/drill/rules.js`) score like `scripts/drill_data.py`, region by region | Yes |
| `test_site.py` | Every page loads with no console errors or failed requests, has no sideways scroll at 390 and 1440 px, works with reduced motion and the keyboard, passes an accessibility scan, works offline after one visit, and prints the area report on one page | Yes |
| `test_research_page.py` | Every number on the Research page matches the committed result files (through `scripts/research_numbers.py`) | Yes |
| `test_open_data.py` | The open data files in `docs/data/` match the alert track record, and the RSS and calendar feeds are valid | No |
| `test_app.py` | The original Streamlit app renders every page without errors, for both panels and both languages (Streamlit's own test runner) | No |
