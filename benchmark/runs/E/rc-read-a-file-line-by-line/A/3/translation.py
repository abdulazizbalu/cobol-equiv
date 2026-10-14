from cobol_equiv.runtime import Storage, Num, Alnum, move, add, SPACES, display_bytes
from cobol_equiv.runtime.files import LineSequentialReader


def _trim(b: bytes) -> bytes:
    i = 0
    n = len(b)
    while i < n and b[i] == 0x20:
        i += 1
    if i == n:
        return b""
    j = n
    while j > i and b[j - 1] == 0x20:
        j -= 1
    return b[i:j]


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()
    rec = Storage("FD", [Alnum("INPUT-RECORD", "X(256)")])
    ws = Storage("WS", [
        Num("INPUT-FILE-STATUS", "99"),
        Num("LINE-COUNT", "9(6)"),
    ])
    move(SPACES, rec["INPUT-RECORD"])

    if "input.txt" not in input_files:
        out += b"The file could not be opened.\n"
        return bytes(out), {}

    reader = LineSequentialReader(input_files["input.txt"], 256)
    status = 0
    move(1, ws["LINE-COUNT"])
    while status != 10:
        saved = rec["INPUT-RECORD"].raw
        r = reader.read(rec["INPUT-RECORD"])
        if r is None:
            rec["INPUT-RECORD"].set_raw(saved)
            status = 10
        else:
            status = 0
        out += display_bytes(ws["LINE-COUNT"]) + b": " + _trim(rec["INPUT-RECORD"].raw) + b"\n"
        add(1, ws["LINE-COUNT"])

    return bytes(out), {}
