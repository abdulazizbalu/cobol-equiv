"""Rosetta Code task "Roman numerals/Encode", solution roman-numerals-encode.cob
(downloaded, not committed). Free format.

ACCEPTs numbers into 9(4) until 0 (or the end of input). Override (domain
stated by the task: a positive integer; the item is PIC 9(4)): decimal text
of 1 .. 9999. No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-roman-numerals-encode",
    area="table lookup through REDEFINES with two-level OCCURS and INDEXED BY, INITIALIZE",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("WS-NUMBER", "X(4)")], 0, 10, overrides={
        "WS-NUMBER": st.integers(1, 9999).map(str),
    })],
)
