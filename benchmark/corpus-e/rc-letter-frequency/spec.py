"""Rosetta Code task "Letter frequency", solution letter-frequency.cob
(downloaded, not committed).

Input File.txt, lines X(80). No overrides (the task allows any text file).
No fixed vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-letter-frequency",
    area="INSPECT TALLYING on FUNCTION UPPER-CASE, MOVE CORRESPONDING, read loop",
    source=HERE / "program.cob",
    inputs=[InputSpec("File.txt", [Alnum("RECORD-NAME", "X(80)")], 0, 12)],
)
