"""Reference translation of benchmark/corpus-e/omp-cbl0001/program.cob."""

from cobol_equiv.runtime import COMP3, Alnum, Edited, Group, Num, Storage, move

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

PRINT_REC = [
    Alnum("ACCT-NO-O", "X(8)"),
    Edited("ACCT-LIMIT-O", "$$,$$$,$$9.99"),
    Edited("ACCT-BALANCE-O", "$$,$$$,$$9.99"),
    Alnum("LAST-NAME-O", "X(20)"),
    Alnum("FIRST-NAME-O", "X(15)"),
    Alnum("COMMENTS-O", "X(50)"),
]


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files["ACCTREC"]
    acct = Storage("ACCT-REC", ACCT_FIELDS)
    prt = Storage("PRINT-LINE", PRINT_REC)
    out = bytearray()
    size = acct.size
    for pos in range(0, len(data) - len(data) % size, size):
        acct.area[:] = data[pos:pos + size]
        move(acct["ACCT-NO"], prt["ACCT-NO-O"])
        move(acct["ACCT-LIMIT"], prt["ACCT-LIMIT-O"])
        move(acct["ACCT-BALANCE"], prt["ACCT-BALANCE-O"])
        move(acct["LAST-NAME"], prt["LAST-NAME-O"])
        move(acct["FIRST-NAME"], prt["FIRST-NAME-O"])
        move(acct["COMMENTS"], prt["COMMENTS-O"])
        out += bytes(prt.area)
    return b"", {"PRTLINE": bytes(out)}
