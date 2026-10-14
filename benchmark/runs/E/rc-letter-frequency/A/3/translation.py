from cobol_equiv.runtime import Storage, Num, Alnum, Edited, move, display_line
from cobol_equiv.runtime.files import LineSequentialReader

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    fd = Storage("FD", [Alnum("Record-Name", "X(80)")])
    rec = fd["Record-Name"]
    disp = Storage("DISP", [Edited(c + "-cnt", "ZZZZ9") for c in LETTERS])
    cnt = Storage("CNT", [Num(c + "-cnt", "9(5)", value=0) for c in LETTERS])

    reader = LineSequentialReader(input_files.get("File.txt", b""), 80)
    counts = {c: 0 for c in LETTERS}
    eof = False
    while not eof:
        saved = rec.raw
        r = reader.read(rec)
        if r is None:
            eof = True
            if rec.raw != saved:
                rec.set_raw(saved)
        data = rec.raw
        up = bytes((b - 32) if 97 <= b <= 122 else b for b in data)
        for c in LETTERS:
            counts[c] = (counts[c] + up.count(c.encode())) % 100000

    for c in LETTERS:
        move(counts[c], cnt[c + "-cnt"])
        move(cnt[c + "-cnt"], disp[c + "-cnt"])

    out = bytearray()
    out += display_line("Letter Frequency Distribution")
    out += display_line("-----------------------------")
    for i in range(13):
        a = LETTERS[i]
        b = LETTERS[i + 13]
        out += display_line(a + " : ", disp[a + "-cnt"], "          ",
                            b + " : ", disp[b + "-cnt"])
    return bytes(out), {}
