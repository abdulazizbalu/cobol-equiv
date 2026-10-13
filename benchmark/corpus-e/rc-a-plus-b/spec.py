"""Rosetta Code task "A+B", solution a+b-1.cob (downloaded, not committed).

The program ACCEPTs A and B on separate lines. The task states the input:
two integers between -1000 and +1000; the generator writes each as decimal
text (override, reason: domain stated by the task). Two lines per input.
No fixed vectors (the task's examples are space-separated pairs on one
line, which this program does not read).
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-a-plus-b",
    area="ACCEPT of signed integers, ADD GIVING",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("NUMBER-TEXT", "X(5)")], 2, 2, overrides={
        "NUMBER-TEXT": st.integers(-1000, 1000).map(str),
    })],
)
