"""Rosetta Code task "Function definition", solution function-definition-2.cob
(downloaded, not committed).

Adapted (adaptation.json): the two arguments of the task, hardcoded as
VALUE 3 and VALUE 2, are read with ACCEPT x and ACCEPT y. Override (domain
stated by the task: two numbers, here PIC 9(3)): decimal text of 0 .. 999.
Two lines per input. No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-function-definition",
    area="user-defined FUNCTION with RETURNING, MULTIPLY GIVING",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("ARG", "X(3)")], 2, 2, overrides={
        "ARG": st.integers(0, 999).map(str),
    })],
)
