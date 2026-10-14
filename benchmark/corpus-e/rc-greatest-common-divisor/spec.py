"""Rosetta Code task "Greatest common divisor", solution
greatest-common-divisor.cob (downloaded, not committed).

Two ACCEPTs into 9(10). Override (domain stated by the task and the
program's prompts: two integers, "max 10 digits"): decimal text of
0 .. 9999999999. Two lines per input. No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-greatest-common-divisor",
    area="Euclid's algorithm with DIVIDE ... REMAINDER",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("NUMBER", "X(10)")], 2, 2, overrides={
        "NUMBER": st.integers(0, 9999999999).map(str),
    })],
)
