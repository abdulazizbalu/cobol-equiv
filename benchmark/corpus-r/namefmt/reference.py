"""Reference Python translation of benchmark/corpus-r/namefmt/program.cob
(MIT licensed)."""

from cobol_equiv.runtime import (SPACES, Alnum, Num, Storage, add, compute, dec, display_line,
                                 inspect_converting, move, refmod, subtract)
from cobol_equiv.runtime.files import LineSequentialReader

NAME_REC = [Alnum("NAME-REC", "X(30)")]
LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def working_storage():
    return Storage("WS", [
        Alnum("WS-TEXT", "X(30)"), Num("WS-LEN", "99"), Num("WS-COMMA", "99"), Num("WS-S", "99"),
        Num("WS-I", "99"), Num("WS-P", "99"), Num("WS-N", "99"), Num("WS-WORDS", "99"),
        Alnum("WS-OUT", "X(40)"),
    ])


def v(ws, name) -> int:
    return int(ws[name].value)


def build_output(ws, out):
    text = ws["WS-TEXT"]
    move(SPACES, ws["WS-OUT"])
    compute(ws["WS-N"], dec(ws["WS-LEN"]) - dec(ws["WS-S"]) + dec(1))
    move(refmod(text, v(ws, "WS-S"), v(ws, "WS-N")), refmod(ws["WS-OUT"], 1, v(ws, "WS-N")))
    inspect_converting(refmod(ws["WS-OUT"], 1, 1), LOWER, UPPER)
    compute(ws["WS-P"], dec(ws["WS-N"]) + dec(2))
    compute(ws["WS-N"], dec(ws["WS-COMMA"]) - dec(1))
    move(refmod(text, 1, v(ws, "WS-N")), refmod(ws["WS-OUT"], v(ws, "WS-P"), v(ws, "WS-N")))
    add(ws["WS-N"], ws["WS-P"])
    subtract(1, ws["WS-P"])
    move(1, ws["WS-WORDS"])
    move(2, ws["WS-I"])
    while not v(ws, "WS-I") > v(ws, "WS-P"):
        i = v(ws, "WS-I")
        if refmod(ws["WS-OUT"], i, 1).raw != b" " and refmod(ws["WS-OUT"], i - 1, 1).raw == b" ":
            add(1, ws["WS-WORDS"])
        add(1, ws["WS-I"])
    out += display_line("[", refmod(ws["WS-OUT"], 1, v(ws, "WS-P")), "] ", ws["WS-WORDS"])


def format_name(ws, out):
    text = ws["WS-TEXT"]
    move(30, ws["WS-LEN"])
    while not (v(ws, "WS-LEN") == 0 or refmod(text, v(ws, "WS-LEN"), 1).raw != b" "):
        subtract(1, ws["WS-LEN"])
    if v(ws, "WS-LEN") == 0:
        out += display_line("EMPTY")
        return
    move(0, ws["WS-COMMA"])
    move(1, ws["WS-I"])
    while not (v(ws, "WS-I") > v(ws, "WS-LEN") or v(ws, "WS-COMMA") > 0):
        if refmod(text, v(ws, "WS-I"), 1).raw == b",":
            move(ws["WS-I"], ws["WS-COMMA"])
        add(1, ws["WS-I"])
    if v(ws, "WS-COMMA") < 2 or v(ws, "WS-COMMA") == v(ws, "WS-LEN"):
        out += display_line("NO SPLIT ", refmod(text, 1, v(ws, "WS-LEN")))
        return
    compute(ws["WS-S"], dec(ws["WS-COMMA"]) + dec(1))
    while not (v(ws, "WS-S") > v(ws, "WS-LEN") or refmod(text, v(ws, "WS-S"), 1).raw != b" "):
        add(1, ws["WS-S"])
    if v(ws, "WS-S") > v(ws, "WS-LEN"):
        out += display_line("NO SPLIT ", refmod(text, 1, v(ws, "WS-LEN")))
    else:
        build_output(ws, out)


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = working_storage()
    rec = Storage("NAME-REC", NAME_REC)
    reader = LineSequentialReader(input_files["NAMES.DAT"], rec.size)
    out = bytearray()
    while reader.read(rec.record()) is not None:
        move(rec["NAME-REC"], ws["WS-TEXT"])  # READ ... INTO
        format_name(ws, out)
    return bytes(out), {}
