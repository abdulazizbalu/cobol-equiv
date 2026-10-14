"""Track R program written for this repository.

Input NAMES.DAT, LINE SEQUENTIAL, one 30-character name per line.
Override (domain stated by the program header, "LAST,FIRST MIDDLE"): three
in four lines are built as letters and spaces, a comma, optional spaces and
more letters and spaces, cut to 30 characters; the others are any text the
generator produces for X(30), which the program also handles.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

RECORD = [Alnum("NAME-REC", "X(30)")]
_PART = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCXYZ ", max_size=14)
_NAME = st.builds(lambda a, sp, b: (a + "," + " " * sp + b)[:30], _PART, st.integers(0, 2), _PART)
_TEXT = st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=30)

SPEC = ProgramSpec(
    name="namefmt",
    area="reference modification as sender and receiver, scanning loops",
    source=HERE / "program.cob",
    inputs=[InputSpec("NAMES.DAT", RECORD, 0, 20, overrides={
        "NAME-REC": st.one_of(_NAME, _NAME, _NAME, _TEXT),
    })],
    vectors=[
        {"NAMES.DAT": b""},
        {"NAMES.DAT": b"smith,john  quincy\n\n,abc\nabc,\nabc,   \nnocomma here\nx,y\n"
                      b"  lead,  trail  sp\n123456789012345678901234567,ab\n"},
    ],
)
