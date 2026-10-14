from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, SPACES,
    display_line, string, unstring, Into, Phrase,
    inspect_tallying, inspect_replacing, inspect_converting,
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
    W = ws.__getitem__
    ln = rec["LN-TEXT"]

    def do_line():
        move(0, W("WS-COMMAS"), W("WS-LEAD-SPACES"), W("WS-AS"), W("WS-NF"),
             W("WS-C1"), W("WS-C2"))
        inspect_tallying(ln, [
            Phrase("ALL", ",", counter=W("WS-COMMAS")),
            Phrase("LEADING", " ", counter=W("WS-LEAD-SPACES")),
        ])
        inspect_tallying(ln, [
            Phrase("ALL", "A", counter=W("WS-AS"), before=","),
        ])
        move(SPACES, W("WS-F1"), W("WS-F2"), W("WS-F3"), W("WS-D1"))
        move("N", W("WS-UOVF"), W("WS-SOVF"))
        move(1, W("WS-PTR"))
        ovf = unstring(ln, [",", (" ", True)], [
            Into(W("WS-F1"), delimiter_in=W("WS-D1"), count_in=W("WS-C1")),
            Into(W("WS-F2"), count_in=W("WS-C2")),
            Into(W("WS-F3")),
        ], pointer=W("WS-PTR"), tallying=W("WS-NF"))
        if ovf:
            move("Y", W("WS-UOVF"))
        inspect_replacing(W("WS-F1"), [
            Phrase("ALL", "A", by="4"),
            Phrase("LEADING", "0", by="*"),
        ])
        inspect_converting(W("WS-F2"), "ABCDE", "abcde")
        inspect_replacing(W("WS-F3"), [
            Phrase("CHARACTERS", by="#", after="B"),
        ])
        move(SPACES, W("WS-OUT"))
        move(1, W("WS-OPTR"))
        sovf = string([
            (W("WS-F2"), " "),
            ("/", None),
            (W("WS-F1"), " "),
            ("/", None),
            (W("WS-F3"), None),
        ], W("WS-OUT"), pointer=W("WS-OPTR"))
        if sovf:
            move("Y", W("WS-SOVF"))
        out.extend(display_line(
            W("WS-COMMAS"), " ", W("WS-LEAD-SPACES"), " ", W("WS-AS"), " ",
            W("WS-NF"), " ", W("WS-PTR"), " ", W("WS-UOVF"), " ",
            "[", W("WS-F1"), "][", W("WS-D1"), "]", W("WS-C1"),
            "[", W("WS-F2"), "]", W("WS-C2"), "[", W("WS-F3"), "] ",
            "[", W("WS-OUT"), "] ", W("WS-OPTR"), " ", W("WS-SOVF"),
        ))

    while W("WS-EOF").raw != b"Y":
        r = reader.read(rec.record())
        if r is None:
            move("Y", W("WS-EOF"))
        else:
            do_line()

    return bytes(out), {}
