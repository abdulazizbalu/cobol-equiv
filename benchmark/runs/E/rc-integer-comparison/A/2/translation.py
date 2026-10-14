from decimal import Decimal

from cobol_equiv.runtime import Storage, Num, Stdin, display_line, display_bytes, DataError


def _cmp(a, b):
    try:
        va = a.value
        vb = b.value
    except (DataError, Exception):
        ra = a.raw
        rb = b.raw
        return (ra > rb) - (ra < rb)
    return (va > vb) - (va < vb)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("A", "9(10)"),
        Num("B", "9(10)"),
    ])
    a = ws["A"]
    b = ws["B"]
    inp = Stdin(stdin)
    out = bytearray()

    out += display_bytes("First number: ")
    inp.accept(a)
    out += display_bytes("Second number: ")
    inp.accept(b)

    c = _cmp(a, b)
    if c < 0:
        out += display_line(a, " is less than ", b)
    elif c == 0:
        out += display_line(a, " is equal to ", b)
    else:
        out += display_line(a, " is larger than ", b)

    return bytes(out), {}
