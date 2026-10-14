"""SRCHBIN from the Open Mainframe Project COBOL Programming Course (CC BY 4.0).

Loads up to 44 ACCTREC records (fixed 170 bytes, two COMP-3 fields) into a
table and searches it; one DISPLAY line. The input layout is the table
entry layout of the program. No generator overrides.
Fixed vector: the course's sample data set (`sample-ACCTREC.bin`, converted
from EBCDIC; see ADAPTATION.md).
"""

from pathlib import Path

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import COMP3, Alnum, Group, Num

HERE = Path(__file__).parent

ACCT_FIELDS = [
    Alnum("ACCT-NO", "X(8)"),
    Num("ACCT-LIMIT", "S9(7)V99", usage=COMP3),
    Num("ACCT-BALANCE", "S9(7)V99", usage=COMP3),
    Alnum("LAST-NAME", "X(20)"),
    Alnum("FIRST-NAME", "X(15)"),
    Group("CLIENT-ADDR", [Alnum("STREET-ADDR", "X(25)"), Alnum("CITY-COUNTY", "X(20)"),
                          Alnum("USA-STATE", "X(15)")]),
    Alnum("RESERVED", "X(7)"),
    Alnum("COMMENTS", "X(50)"),
]

SPEC = ProgramSpec(
    name="omp-srchbin",
    area="table loaded from a file, SEARCH ALL (binary search)",
    source=HERE / "program.cob",
    inputs=[InputSpec("ACCTREC", ACCT_FIELDS, 0, 50, organization="record")],
    vectors=[{"ACCTREC": (HERE / "sample-ACCTREC.bin").read_bytes()}],
)
