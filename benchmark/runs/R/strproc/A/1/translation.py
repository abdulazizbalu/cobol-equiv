from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, SPACES,
    inspect_tallying, inspect_replacing, inspect_converting, Phrase,
    unstring, Into, string, display_line,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    rec = Storage("LINE-REC", [
        Group("LINE-REC", [Alnum("LN-TEXT", "X(30)")]),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-COMMAS", "99"),
        Num("WS-LEAD-SPACES", "99"),
        Num("WS-AS", "99"),
        Alnum("WS-F1", "X(8)"),
        Alnum("WS-F2", "X(8)"),
        Alnum("WS-F3", "X(6)"),
        Num("WS-C1", "99"),
        Num("WS-C2", "99"),
        Alnum("WS-D1", "X"),
        Num("WS-PTR", "99"),
        Num("WS-NF", "99"),
        Alnum("WS-UOVF", "X"),
        Alnum("WS-OUT", "X(16)"),
        Num("WS-OPTR", "99"),
        Alnum("WS-SOVF", "X"),
    ])
    out = bytearray()
    reader = LineSequentialReader(input_files.get("LINES.DAT", b""), 30)
    ln = rec["LN-TEXT"]
    f1, f2, f3 = ws["WS-F1"], ws["WS-F2"], ws["WS-F3"]
    d1 = ws["WS-D1"]

    def do_line():
        move(0, ws["WS-COMMAS"], ws["WS-LEAD-SPACES"], ws["WS-AS"],
             ws["WS-NF"], ws["WS-C1"], ws["WS-C2"])
        inspect_tallying(ln, [
            Phrase("ALL", ",", counter=ws["WS-COMMAS"]),
            Phrase("LEADING", " ", counter=ws["WS-LEAD-SPACES"]),
        ])
        inspect_tallying(ln, [
            Phrase("ALL", "A", counter=ws["WS-AS"], before=","),
        ])
        move(SPACES, f1, f2, f3, d1)
        move("N", ws["WS-UOVF"], ws["WS-SOVF"])
        move(1, ws["WS-PTR"])
        if unstring(ln, [",", (" ", True)],
                    [Into(f1, delimiter_in=d1, count_in=ws["WS-C1"]),
                     Into(f2, count_in=ws["WS-C2"]),
                     f3],
                    pointer=ws["WS-PTR"], tallying=ws["WS-NF"]):
            move("Y", ws["WS-UOVF"])
        inspect_replacing(f1, [
            Phrase("ALL", "A", by="4"),
            Phrase("LEADING", "0", by="*"),
        ])
        inspect_converting(f2, "ABCDE", "abcde")
        inspect_replacing(f3, [Phrase("CHARACTERS", by="#", after="B")])
        move(SPACES, ws["WS-OUT"])
        move(1, ws["WS-OPTR"])
        if string([(f2, " "), ("/", None), (f1, " "), ("/", None), (f3, None)],
                  ws["WS-OUT"], pointer=ws["WS-OPTR"]):
            move("Y", ws["WS-SOVF"])
        out.extend(display_line(
            ws["WS-COMMAS"], " ", ws["WS-LEAD-SPACES"], " ", ws["WS-AS"], " ",
            ws["WS-NF"], " ", ws["WS-PTR"], " ", ws["WS-UOVF"], " ",
            "[", f1, "][", d1, "]", ws["WS-C1"],
            "[", f2, "]", ws["WS-C2"], "[", f3, "] ",
            "[", ws["WS-OUT"], "] ", ws["WS-OPTR"], " ", ws["WS-SOVF"]))

    while ws["WS-EOF"].text != "Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", ws["WS-EOF"])
        else:
            do_line()
    return bytes(out), {}
