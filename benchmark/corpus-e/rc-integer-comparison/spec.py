"""Rosetta Code task "Integer comparison", solution integer-comparison.cob
(downloaded, not committed).

Two ACCEPTs into 9(10). Override (domain stated by the task: two
integers): decimal text of -9999999999 .. 9999999999. Two lines per input.
No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-integer-comparison",
    area="ACCEPT into unsigned items, nested IF / ELSE IF comparisons",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("NUMBER", "X(11)")], 2, 2, overrides={
        "NUMBER": st.integers(-9999999999, 9999999999).map(str),
    })],
)
