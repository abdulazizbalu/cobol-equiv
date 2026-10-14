"""Reference Python translation of benchmark/corpus-r/wordwrap/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (SPACES, Alnum, Into, Num, Storage, add, compute, dec,
                                 display_line, move, refmod, string, unstring)
from cobol_equiv.runtime.files import LineSequentialReader

TEXT_REC = [Num("TX-WIDTH", "99"), Alnum("TX-TEXT", "X(60)")]


def working_storage():
    return Storage("WS", [
        Num("WS-PTR", "99"), Alnum("WS-WORD", "X(60)"), Num("WS-WLEN", "99"), Alnum("WS-LINE", "X(40)"),
        Num("WS-LPTR", "99"), Num("WS-USED", "99"), Num("WS-START", "99"), Num("WS-PART", "99"),
        Num("WS-LINES", "9(3)", value=0),
    ])


def v(ws, name) -> int:
    return int(ws[name].value)


def flush_line(tx, ws, out):
    add(1, ws["WS-LINES"])
    out += display_line("|", refmod(ws["WS-LINE"], 1, int(tx["TX-WIDTH"].value)), "|")
    move(SPACES, ws["WS-LINE"])
    move(0, ws["WS-USED"])


def place_word(tx, ws, out):
    width = int(tx["TX-WIDTH"].value)
    move(1, ws["WS-START"])
    while not v(ws, "WS-WLEN") - v(ws, "WS-START") < width:
        if v(ws, "WS-USED") > 0:
            flush_line(tx, ws, out)
        move(refmod(ws["WS-WORD"], v(ws, "WS-START"), width - 1), ws["WS-LINE"])
        move("-", refmod(ws["WS-LINE"], width, 1))
        move(tx["TX-WIDTH"], ws["WS-USED"])
        flush_line(tx, ws, out)
        compute(ws["WS-START"], dec(ws["WS-START"]) + dec(tx["TX-WIDTH"]) - dec(1))
    compute(ws["WS-PART"], dec(ws["WS-WLEN"]) - dec(ws["WS-START"]) + dec(1))
    if v(ws, "WS-USED") > 0 and v(ws, "WS-USED") + 1 + v(ws, "WS-PART") > width:
        flush_line(tx, ws, out)
    if v(ws, "WS-USED") == 0:
        move(1, ws["WS-LPTR"])
    else:
        compute(ws["WS-LPTR"], dec(ws["WS-USED"]) + dec(2))
    string([(refmod(ws["WS-WORD"], v(ws, "WS-START"), v(ws, "WS-PART")), None)], ws["WS-LINE"],
           pointer=ws["WS-LPTR"])
    compute(ws["WS-USED"], dec(ws["WS-LPTR"]) - dec(1))


def wrap_text(tx, ws, out):
    width = tx["TX-WIDTH"].value
    if width < 5 or width > 40:
        out += display_line("BAD WIDTH ", tx["TX-WIDTH"])
        return
    out += display_line("WIDTH ", tx["TX-WIDTH"])
    move(SPACES, ws["WS-LINE"])
    move(0, ws["WS-USED"])
    move(1, ws["WS-PTR"])
    while not v(ws, "WS-PTR") > 60:
        move(SPACES, ws["WS-WORD"])
        move(0, ws["WS-WLEN"])
        unstring(tx["TX-TEXT"], [(" ", True)], [Into(ws["WS-WORD"], count_in=ws["WS-WLEN"])],
                 pointer=ws["WS-PTR"])
        if v(ws, "WS-WLEN") > 0:
            place_word(tx, ws, out)
    if v(ws, "WS-USED") > 0:
        flush_line(tx, ws, out)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    tx = Storage("TEXT-REC", TEXT_REC)
    reader = LineSequentialReader(input_files["TEXT.DAT"], tx.size)
    out = bytearray()
    while reader.read(tx.record()) is not None:
        wrap_text(tx, ws, out)
    out += display_line("LINES ", ws["WS-LINES"])
    return bytes(out), {}
