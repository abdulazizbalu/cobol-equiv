from cobol_equiv.runtime import Storage, Group, Num, Alnum, Edited, COMP3, move
from cobol_equiv.runtime.files import RecordSequentialReader, RecordSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    print_rec = Storage("PRINT-REC", [
        Alnum("ACCT-NO-O", "X(8)"),
        Edited("ACCT-LIMIT-O", "$$,$$$,$$9.99"),
        Edited("ACCT-BALANCE-O", "$$,$$$,$$9.99"),
        Alnum("LAST-NAME-O", "X(20)"),
        Alnum("FIRST-NAME-O", "X(15)"),
        Alnum("COMMENTS-O", "X(50)"),
    ])
    acct = Storage("ACCT-FIELDS", [
        Alnum("ACCT-NO", "X(8)"),
        Num("ACCT-LIMIT", "S9(7)V99", usage=COMP3),
        Num("ACCT-BALANCE", "S9(7)V99", usage=COMP3),
        Alnum("LAST-NAME", "X(20)"),
        Alnum("FIRST-NAME", "X(15)"),
        Group("CLIENT-ADDR", [
            Alnum("STREET-ADDR", "X(25)"),
            Alnum("CITY-COUNTY", "X(20)"),
            Alnum("USA-STATE", "X(15)"),
        ]),
        Alnum("RESERVED", "X(7)"),
        Alnum("COMMENTS", "X(50)"),
    ])
    ws = Storage("FLAGS", [Alnum("LASTREC", "X", value=" ")])

    reader = RecordSequentialReader(input_files.get("ACCTREC", b""), 170)
    writer = RecordSequentialWriter()

    def read_record():
        if reader.read(acct.record()) is None:
            move("Y", ws["LASTREC"])

    def write_record():
        move(acct["ACCT-NO"], print_rec["ACCT-NO-O"])
        move(acct["ACCT-LIMIT"], print_rec["ACCT-LIMIT-O"])
        move(acct["ACCT-BALANCE"], print_rec["ACCT-BALANCE-O"])
        move(acct["LAST-NAME"], print_rec["LAST-NAME-O"])
        move(acct["FIRST-NAME"], print_rec["FIRST-NAME-O"])
        move(acct["COMMENTS"], print_rec["COMMENTS-O"])
        writer.write(print_rec.record())

    read_record()
    while ws["LASTREC"].raw != b"Y":
        write_record()
        read_record()

    return b"", {"PRTLINE": writer.getvalue()}
