"""Rosetta Code task "File input/output", solution file-input-output-1.cob
(downloaded, not committed).

input.txt and output.txt are ORGANIZATION SEQUENTIAL with 80-byte records.
No overrides (the task allows any content). No fixed vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-file-input-output",
    area="record sequential copy through READ INTO / WRITE FROM",
    source=HERE / "program.cob",
    inputs=[InputSpec("input.txt", [Alnum("INPUT-RECORD", "X(80)")], 0, 10,
                      organization="record")],
    outputs=["output.txt"],
    layouts={"output.txt": OutputLayout(lambda rec: [("OUTPUT-RECORD", 0, 80)], record_length=80)},
)
