from cobol_equiv.runtime import (
    Storage, Num, Alnum, Edited, Group, move, display_line,
    Phrase, inspect_tallying,
)
from cobol_equiv.runtime.files import LineSequentialReader

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    fd = Storage("FD", [Alnum("Record-Name", "X(80)")])
    ws = Storage("WS", [Alnum("Eof", "X", value="F")])
    cnt = Storage("CNT", [
        Group("Letter-cnt", [Num(f"{c}-cnt", "9(5)", value=0) for c in LETTERS])
    ])
    disp = Storage("DISP", [
        Group("Letter-disp", [Edited(f"{c}-cnt", "ZZZZ9") for c in LETTERS])
    ])
    tmp = Storage("TMP", [Alnum("UP", "X(80)")])

    rec = fd["Record-Name"]
    reader = LineSequentialReader(input_files.get("File.txt", b""), 80)

    while ws["Eof"].raw != b"T":
        r = reader.read(rec)
        if r is None:
            move("T", ws["Eof"])
        raw = rec.raw
        up = bytes((b - 32) if 97 <= b <= 122 else b for b in raw)
        tmp["UP"].set_raw(up)
        for c in LETTERS:
            inspect_tallying(tmp["UP"], [Phrase("ALL", c, counter=cnt[f"{c}-cnt"])])

    for c in LETTERS:
        move(cnt[f"{c}-cnt"], disp[f"{c}-cnt"])

    out = bytearray()
    out += display_line("Letter Frequency Distribution")
    out += display_line("-----------------------------")
    for i in range(13):
        a = LETTERS[i]
        b = LETTERS[i + 13]
        out += display_line(f"{a} : ", disp[f"{a}-cnt"], "          ",
                            f"{b} : ", disp[f"{b}-cnt"])
    return bytes(out), {}
