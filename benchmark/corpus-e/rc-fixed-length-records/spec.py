"""Rosetta Code task "Fixed length records", solution fixed-length-records-1.cob
(downloaded, not committed).

infile.dat and outfile.dat are ORGANIZATION SEQUENTIAL with 80-byte
records. No overrides. No fixed vectors (the task describes how to make a
sample file but does not give one).
"""

from pathlib import Path

from cobol_equiv.harness.spec import InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-fixed-length-records",
    area="record sequential I/O, FUNCTION REVERSE, reopening an output file for input",
    source=HERE / "program.cob",
    inputs=[InputSpec("infile.dat", [Alnum("INPUT-TEXT", "X(80)")], 0, 10,
                      organization="record")],
    outputs=["outfile.dat"],
    layouts={"outfile.dat": OutputLayout(lambda rec: [("OUTPUT-TEXT", 0, 80)], record_length=80)},
)
