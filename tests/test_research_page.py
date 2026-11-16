"""The Research page (site/research.html) shows the numbers in the committed result files.

Every research number on the page sits in an element with a `data-k` key. scripts/research_numbers.py recomputes
each key from research/results/ and research/analysis/out/; this compares the two. It also checks the two numbers
the methodology page quotes from the research, and that the method table marks the lowest of the four in each row.
"""
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("research_numbers", ROOT / "scripts" / "research_numbers.py")
research_numbers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research_numbers)

PAGE = (ROOT / "site" / "research.html").read_text(encoding="utf-8")
SHOWN = re.findall(r'data-k="([^"]+)">([^<]*)<', PAGE)
EXPECTED = research_numbers.numbers()


def test_page_has_research_numbers():
    assert len(SHOWN) > 100


@pytest.mark.parametrize("key,text", SHOWN, ids=[f"{k}:{n}" for n, (k, _) in enumerate(SHOWN)])
def test_number_matches_results(key, text):
    assert key in EXPECTED, f"{key} is not computed by scripts/research_numbers.py"
    assert text == EXPECTED[key]


def test_headline_counts_cover_all_checks():
    assert sum(int(EXPECTED[f"wins-{m}"]) for m in research_numbers.FOUR) == 24
    assert EXPECTED["studies"] == "19"


def test_method_table_marks_the_lowest_of_the_four():
    import pandas as pd
    mc = pd.read_csv(ROOT / "research" / "results" / "model_comparison.csv")
    mc = mc[(mc.horizon == 4) & mc.model.isin(research_numbers.FOUR)]
    for panel, year in research_numbers.SETS:
        best = mc[(mc.panel == panel) & (mc.test_year == year)].set_index("model").mae.idxmin()
        marked = re.findall(rf'class="num best[^"]*" data-th="[^"]+"><span data-k="rel-{panel}-{year}-(\w+)"', PAGE)
        assert marked == [best], f"{panel} {year}: marked {marked}, lowest is {best}"


def test_methodology_quotes_the_same_wins():
    text = (ROOT / "site" / "methodology.html").read_text(encoding="utf-8")
    others = max(int(EXPECTED[f"wins-{m}"]) for m in research_numbers.FOUR if m != "lightgbm")
    assert f"lowest error in {EXPECTED['wins-lightgbm']} of 24 checks, and no other method in more than {others}" in text
