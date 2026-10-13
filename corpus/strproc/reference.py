"""Reference Python translation of corpus/strproc/program.cob (MIT licensed)."""

from cobol_equiv.runtime import (SPACES, Alnum, Into, Num, Phrase, Storage, display_line,
                                 inspect_converting, inspect_replacing, inspect_tallying, move,
                                 string, unstring)
from cobol_equiv.runtime.files import LineSequentialReader


def working_storage():
    return Storage("WS", [
        Num("WS-COMMAS", "99"), Num("WS-LEAD-SPACES", "99"), Num("WS-AS", "99"),
        Alnum("WS-F1", "X(8)"), Alnum("WS-F2", "X(8)"), Alnum("WS-F3", "X(6)"),
        Num("WS-C1", "99"), Num("WS-C2", "99"), Alnum("WS-D1", "X"),
        Num("WS-PTR", "99"), Num("WS-NF", "99"), Alnum("WS-UOVF", "X"),
        Alnum("WS-OUT", "X(16)"), Num("WS-OPTR", "99"), Alnum("WS-SOVF", "X"),
    ])


def do_line(ln, ws, out):
    f = ws.f
    move(0, f("WS-COMMAS"), f("WS-LEAD-SPACES"), f("WS-AS"), f("WS-NF"), f("WS-C1"), f("WS-C2"))
    text = ln["LN-TEXT"]
    inspect_tallying(text, [Phrase("ALL", ",", counter=f("WS-COMMAS")),
                            Phrase("LEADING", " ", counter=f("WS-LEAD-SPACES"))])
    inspect_tallying(text, [Phrase("ALL", "A", counter=f("WS-AS"), before=",")])
    move(SPACES, f("WS-F1"), f("WS-F2"), f("WS-F3"), f("WS-D1"))
    move("N", f("WS-UOVF"), f("WS-SOVF"))
    move(1, f("WS-PTR"))
    if unstring(text, [",", (" ", True)],
                [Into(f("WS-F1"), f("WS-D1"), f("WS-C1")), Into(f("WS-F2"), count_in=f("WS-C2")),
                 f("WS-F3")],
                pointer=f("WS-PTR"), tallying=f("WS-NF")):
        move("Y", f("WS-UOVF"))
    inspect_replacing(f("WS-F1"), [Phrase("ALL", "A", by="4"), Phrase("LEADING", "0", by="*")])
    inspect_converting(f("WS-F2"), "ABCDE", "abcde")
    inspect_replacing(f("WS-F3"), [Phrase("CHARACTERS", by="#", after="B")])
    move(SPACES, f("WS-OUT"))
    move(1, f("WS-OPTR"))
    if string([(f("WS-F2"), SPACES), ("/", None), (f("WS-F1"), " "), ("/", None), (f("WS-F3"), None)],
              f("WS-OUT"), pointer=f("WS-OPTR")):
        move("Y", f("WS-SOVF"))
    out += display_line(f("WS-COMMAS"), " ", f("WS-LEAD-SPACES"), " ", f("WS-AS"), " ",
                        f("WS-NF"), " ", f("WS-PTR"), " ", f("WS-UOVF"), " ",
                        "[", f("WS-F1"), "][", f("WS-D1"), "]", f("WS-C1"),
                        "[", f("WS-F2"), "]", f("WS-C2"), "[", f("WS-F3"), "] ",
                        "[", f("WS-OUT"), "] ", f("WS-OPTR"), " ", f("WS-SOVF"))


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    ln = Storage("LINE-REC", [Alnum("LN-TEXT", "X(30)")])
    reader = LineSequentialReader(input_files["LINES.DAT"], ln.size)
    out = bytearray()
    while reader.read(ln.record()) is not None:
        do_line(ln, ws, out)
    return bytes(out), {}
