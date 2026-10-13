"""CBL0001 from the Open Mainframe Project COBOL Programming Course (CC BY 4.0).

Reads ACCTREC (fixed 170-byte records with two COMP-3 fields) and writes one
119-byte record per account to PRTLINE. No generator overrides.
Fixed vector: the course's sample data set (`sample-ACCTREC.bin`, converted
from EBCDIC; see ADAPTATION.md).
"""

from pathlib import Path

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import InputSpec, OutputLayout, ProgramSpec
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

PRINT_REC = columns(("ACCT-NO-O", 8), ("ACCT-LIMIT-O", 13), ("ACCT-BALANCE-O", 13),
                    ("LAST-NAME-O", 20), ("FIRST-NAME-O", 15), ("COMMENTS-O", 50))

SPEC = ProgramSpec(
    name="omp-cbl0001",
    area="sequential file copy with COMP-3 input and floating $ editing",
    source=HERE / "program.cob",
    inputs=[InputSpec("ACCTREC", ACCT_FIELDS, 0, 20, organization="record")],
    outputs=["PRTLINE"],
    layouts={"PRTLINE": OutputLayout(lambda rec: PRINT_REC, record_length=119)},
    vectors=[{"ACCTREC": (HERE / "sample-ACCTREC.bin").read_bytes()}],
)
