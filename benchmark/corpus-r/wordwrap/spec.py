"""Track R program written for this repository.

Input TEXT.DAT, LINE SEQUENTIAL. Overrides: TX-WIDTH 3 .. 42 (domain
stated by the program's validation, 5-40, plus invalid values on each
side); TX-TEXT: three in four values are words of 1-25 letters separated
by 1-3 spaces, cut to 60 characters (the program header: "words"); the
others are any text the generator produces for X(60).
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Num("TX-WIDTH", "99"), Alnum("TX-TEXT", "X(60)")]
_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=25)
_WORDS = st.lists(st.tuples(st.integers(0, 3), _WORD), max_size=12).map(
    lambda ws: "".join(" " * sp + w for sp, w in ws)[:60])
_TEXT = st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=60)

SPEC = ProgramSpec(
    name="wordwrap",
    area="UNSTRING and STRING WITH POINTER, reference modification, nested PERFORM UNTIL",
    source=HERE / "program.cob",
    inputs=[InputSpec("TEXT.DAT", RECORD, 0, 8, overrides={
        "TX-WIDTH": st.integers(3, 42),
        "TX-TEXT": st.one_of(_WORDS, _WORDS, _WORDS, _TEXT),
    })],
    vectors=[
        {"TEXT.DAT": b""},
        {"TEXT.DAT": b"10the quick brown fox jumps over the lazy dog\n05abcdefghijklmnopqrstuvwxyz ab c\n"
                     b"04x\n40\n12   lead   and   trail   \n06abcde abcdef abcdefg\n"},
    ],
)
