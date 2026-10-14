from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, subtract, compute, dec,
    unstring, display_line, display_bytes, Stdin,
)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("FIBONACCI-PROCESSING", [
            Num("FIBONACCI-NUMBER", "9(36)", value=0),
            Num("FIB-ONE", "9(36)", value=0),
            Num("FIB-TWO", "9(36)", value=1),
        ]),
        Num("DESIRED-COUNT", "9(4)"),
        Group("FORMATTING", [
            Edited("INTERM-RESULT", "Z(35)9"),
            Alnum("FORMATTED-RESULT", "X(36)"),
            Alnum("FORMATTED-SPACE", "X(35)"),
        ]),
    ])
    tmp = Storage("TMP", [Alnum("SRC-COPY", "X(36)")])

    out = bytearray()
    inp = Stdin(stdin)

    fib = ws["FIBONACCI-NUMBER"]
    one = ws["FIB-ONE"]
    two = ws["FIB-TWO"]
    cnt = ws["DESIRED-COUNT"]
    interm = ws["INTERM-RESULT"]
    fres = ws["FORMATTED-RESULT"]
    fspace = ws["FORMATTED-SPACE"]
    src = tmp["SRC-COPY"]

    def format_and_display():
        move(fib, interm)
        move(interm, fres)
        move(fres, src)
        unstring(src, [(" ", True)], [fspace, fres])
        out.extend(display_line(fres))

    out.extend(display_bytes(
        "What place of the Fibonacci Sequence would you like (<173)? "))
    inp.accept(cnt)

    if int(cnt) < 1:
        return bytes(out), {}
    if int(cnt) < 2:
        format_and_display()
        return bytes(out), {}

    subtract(1, cnt)
    format_and_display()
    while int(cnt) != 0:
        compute(fib, dec(one) + dec(two))
        move(two, one)
        move(fib, two)
        subtract(1, cnt)
        format_and_display()

    return bytes(out), {}
