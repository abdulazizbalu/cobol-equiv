"""Rosetta Code task "String case", solution string-case-1.cob (downloaded,
not committed).

Adapted (adaptation.json): the task's input string, hardcoded as
VALUE "alphaBETA", is read with ACCEPT example. No overrides (the task's
input is a string). No fixed vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-string-case",
    area="FUNCTION LOWER-CASE / UPPER-CASE, INSPECT CONVERTING",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("EXAMPLE", "X(9)")], 1, 1)],
)
