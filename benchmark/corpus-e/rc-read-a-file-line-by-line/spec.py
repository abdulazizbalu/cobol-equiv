"""Rosetta Code task "Read a file line by line", solution
read-a-file-line-by-line.cob (downloaded, not committed).

Input input.txt, lines X(256). No overrides (the task allows any text
file). No fixed vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-read-a-file-line-by-line",
    area="READ loop driven by FILE STATUS, PERFORM VARYING, FUNCTION TRIM",
    source=HERE / "program.cob",
    inputs=[InputSpec("input.txt", [Alnum("INPUT-RECORD", "X(256)")], 0, 12)],
)
