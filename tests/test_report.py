from pathlib import Path

from cobol_equiv.report import build

ROOT = Path(__file__).resolve().parents[1]


def test_summary_is_generated_from_committed_csv():
    committed = (ROOT / "results" / "SUMMARY.md").read_text(encoding="utf-8")
    assert committed == build(ROOT / "results"), "run: python -m cobol_equiv.report"
