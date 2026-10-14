"""Rosetta Code task "Binary digits", solution binary-digits-1.cob
(downloaded, not committed).

ACCEPTs one line into X(7) and MOVEs it to 9(7). Override (domain stated by
the task: a non-negative integer): decimal text of 0 .. 9999999. No fixed
vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-binary-digits",
    area="DIVIDE REMAINDER loop, STRING with DELIMITED BY SPACE",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("NSTR", "X(7)")], 1, 1, overrides={
        "NSTR": st.integers(0, 9999999).map(str),
    })],
)
