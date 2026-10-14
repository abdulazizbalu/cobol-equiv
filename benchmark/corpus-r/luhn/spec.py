"""Track R program written for this repository.

Input CARDS.DAT, LINE SEQUENTIAL. Override (domain stated by the program
header: card numbers as digits left-justified in X(16)): three in four
lines are 0-16 decimal digits; the others are any text the generator
produces for X(16), which the program rejects or reports.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

RECORD = [Alnum("CD-NUMBER", "X(16)")]
_DIGITS = st.text(alphabet="0123456789", max_size=16)
_TEXT = st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=16)

SPEC = ProgramSpec(
    name="luhn",
    area="reference modification in loops, class test, INSPECT TALLYING, DIVIDE REMAINDER",
    source=HERE / "program.cob",
    inputs=[InputSpec("CARDS.DAT", RECORD, 0, 20, overrides={
        "CD-NUMBER": st.one_of(_DIGITS, _DIGITS, _DIGITS, _TEXT),
    })],
    vectors=[
        {"CARDS.DAT": b""},
        {"CARDS.DAT": b"4539578763621486\n4539578763621487\n1\n\n12a4\n 123\n79927398713\n"
                      b"9999999999999999\n00\n"},
    ],
)
