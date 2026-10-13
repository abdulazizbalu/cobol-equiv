from pathlib import Path

from cobol_equiv.report import build

ROOT = Path(__file__).resolve().parents[1]


def test_summary_is_generated_from_committed_csv():
    committed = (ROOT / "results" / "SUMMARY.md").read_text(encoding="utf-8")
    assert committed == build(ROOT / "results"), "run: python -m cobol_equiv.report"


def test_readme_numbers_come_from_results():
    from cobol_equiv.report import END, START, readme_block

    text = (ROOT / "README.md").read_text(encoding="utf-8")
    block = text[text.index(START):text.index(END) + len(END)]
    assert block == readme_block(ROOT / "results"), "run: python -m cobol_equiv.report"
