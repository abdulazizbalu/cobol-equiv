from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, display_line,
    inspect_tallying, Phrase,
)
from cobol_equiv.runtime.files import LineSequentialReader

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _upper(b: bytes) -> bytes:
    return bytes((c - 32) if 97 <= c <= 122 else c for c in b)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("REC", [Alnum("Record-Name", "X(80)")])
    tmp = Storage("TMP", [Alnum("UP", "X(80)")])
    ws_eof = Storage("WS1", [Alnum("Eof", "X", value="F")])
    cnt = Storage("CNT", [
        Group("Letter-cnt", [Num(f"{c}-cnt", "9(5)", value=0) for c in LETTERS])
    ])
    disp = Storage("DISP", [
        Group("Letter-disp", [Edited(f"{c}-cnt", "ZZZZ9") for c in LETTERS])
    ])

    reader = LineSequentialReader(input_files.get("File.txt", b""), 80)

    while ws_eof["Eof"].text != "T":
        r = reader.read(rec["Record-Name"])
        if r is None:
            move("T", ws_eof["Eof"])
        for c in LETTERS:
            move(_upper(rec["Record-Name"].raw), tmp["UP"])
            inspect_tallying(tmp["UP"], [Phrase("ALL", c, counter=cnt[f"{c}-cnt"])])

    for c in LETTERS:
        move(cnt[f"{c}-cnt"], disp[f"{c}-cnt"])

    out += display_line("Letter Frequency Distribution")
    out += display_line("-----------------------------")
    for i in range(13):
        a = LETTERS[i]
        b = LETTERS[i + 13]
        out += display_line(f"{a} : ", disp[f"{a}-cnt"], "          ",
                            f"{b} : ", disp[f"{b}-cnt"])

    return bytes(out), {}
