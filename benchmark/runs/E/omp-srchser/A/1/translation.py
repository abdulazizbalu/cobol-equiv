from cobol_equiv.runtime import Storage, Group, Num, Alnum, COMP, COMP3, move, display_line
from cobol_equiv.runtime.files import RecordSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    fd = Storage("ACCT-REC", [Alnum("ACCT-FIELDS", "X(170)")])
    ws = Storage("WS", [
        Group("FLAGS", [
            Alnum("LASTREC", "X", value=" "),
            Num("TABLE-VAR", "S9(4)", usage=COMP),
            Num("TABLE-MAX", "S9(4)", usage=COMP, value=45),
        ]),
        Group("ACCT-TABLE", [
            Group("ACCT-TABLE-ITEM", [
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
            ], occurs=45),
        ]),
    ])

    reader = RecordSequentialReader(input_files.get("ACCTREC", b""), 170)
    eof = False

    def read_record():
        nonlocal eof
        r = reader.read(fd["ACCT-FIELDS"])
        if r is None:
            eof = True
            move("Y", ws["LASTREC"])

    read_record()
    table_var = 1
    table_max = 45
    while not (table_var == table_max or eof):
        move(fd["ACCT-FIELDS"], ws.f("ACCT-TABLE-ITEM", table_var))
        read_record()
        table_var += 1
    move(table_var, ws["TABLE-VAR"])

    target = b"ROOSEVELT".ljust(20, b" ")
    found = False
    for idx in range(1, 46):
        if ws.f("LAST-NAME", idx).raw == target:
            found = True
            break
    if found:
        out += display_line("Roosevelt is found!")
    else:
        out += display_line("Not Found")

    return bytes(out), {}
