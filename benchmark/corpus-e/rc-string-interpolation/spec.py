"""Rosetta Code task "String interpolation (included)", solution
string-interpolation-included-.cob (downloaded, not committed).

Adapted (adaptation.json): the value to insert, hardcoded as
VALUE "little", is read with ACCEPT extra. No overrides (the task's value
is a string). No fixed vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-string-interpolation",
    area="FUNCTION SUBSTITUTE with an X(6) item",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("EXTRA", "X(6)")], 1, 1)],
)
