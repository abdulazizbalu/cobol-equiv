"""Rosetta Code task "Input loop", solution input-loop.cob (downloaded, not
committed).

Reads standard input (ASSIGN TO KEYBOARD, LINE SEQUENTIAL) into X(80) and
DISPLAYs each record. No overrides (the task allows any text). No fixed
vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-input-loop",
    area="LINE SEQUENTIAL read from standard input, PERFORM UNTIL EXIT",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("STREAM-LINE", "X(80)")], 0, 12)],
)
