"""Rosetta Code task "Fibonacci sequence", solution fibonacci-sequence-1.cob
(downloaded, not committed). Free format.

One ACCEPT into 9(4). Override (domain stated by the program's prompt:
"(<173)"): decimal text of 0 .. 172. No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-fibonacci-sequence",
    area="36-digit arithmetic, edited move, UNSTRING DELIMITED BY ALL SPACES",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("DESIRED-COUNT", "X(4)")], 1, 1, overrides={
        "DESIRED-COUNT": st.integers(0, 172).map(str),
    })],
)
