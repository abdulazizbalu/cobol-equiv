from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, compute, dec, display_line,
    unstring, Into, string, refmod, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    out = bytearray()

    fd = Storage("TEXT-FILE", [
        Group("TEXT-REC", [
            Num("TX-WIDTH", "99"),
            Alnum("TX-TEXT", "X(60)"),
        ]),
    ])
    ws = Storage("WS", [
        Alnum("WS-EOF", "X", value="N"),
        Num("WS-PTR", "99"),
        Alnum("WS-WORD", "X(60)"),
        Num("WS-WLEN", "99"),
        Alnum("WS-LINE", "X(40)"),
        Num("WS-LPTR", "99"),
        Num("WS-USED", "99"),
        Num("WS-START", "99"),
        Num("WS-PART", "99"),
        Num("WS-LINES", "9(3)", value=0),
    ])

    rec = fd["TEXT-REC"]
    tx_width = fd["TX-WIDTH"]
    tx_text = fd["TX-TEXT"]
    ws_eof = ws["WS-EOF"]
    ws_ptr = ws["WS-PTR"]
    ws_word = ws["WS-WORD"]
    ws_wlen = ws["WS-WLEN"]
    ws_line = ws["WS-LINE"]
    ws_lptr = ws["WS-LPTR"]
    ws_used = ws["WS-USED"]
    ws_start = ws["WS-START"]
    ws_part = ws["WS-PART"]
    ws_lines = ws["WS-LINES"]

    def flush_line():
        compute(ws_lines, dec(ws_lines) + 1)
        out.extend(display_line("|", refmod(ws_line, 1, int(tx_width)), "|"))
        move(SPACES, ws_line)
        move(0, ws_used)

    def place_word():
        move(1, ws_start)
        while not (ws_wlen.value - ws_start.value < tx_width.value):
            if ws_used.value > 0:
                flush_line()
            move(refmod(ws_word, int(ws_start), int(tx_width) - 1), ws_line)
            move("-", refmod(ws_line, int(tx_width), 1))
            move(tx_width, ws_used)
            flush_line()
            compute(ws_start, dec(ws_start) + dec(tx_width) - 1)
        compute(ws_part, dec(ws_wlen) - dec(ws_start) + 1)
        if ws_used.value > 0 and ws_used.value + 1 + ws_part.value > tx_width.value:
            flush_line()
        if ws_used.value == 0:
            move(1, ws_lptr)
        else:
            compute(ws_lptr, dec(ws_used) + 2)
        string([(refmod(ws_word, int(ws_start), int(ws_part)), None)],
               ws_line, pointer=ws_lptr)
        compute(ws_used, dec(ws_lptr) - 1)

    def wrap_text():
        w = tx_width.value
        if w < 5 or w > 40:
            out.extend(display_line("BAD WIDTH ", tx_width))
        else:
            out.extend(display_line("WIDTH ", tx_width))
            move(SPACES, ws_line)
            move(0, ws_used)
            move(1, ws_ptr)
            while not (ws_ptr.value > 60):
                move(SPACES, ws_word)
                move(0, ws_wlen)
                unstring(tx_text, [(" ", True)],
                         [Into(ws_word, count_in=ws_wlen)],
                         pointer=ws_ptr)
                if ws_wlen.value > 0:
                    place_word()
            if ws_used.value > 0:
                flush_line()

    reader = LineSequentialReader(input_files.get("TEXT.DAT", b""), 62)
    while ws_eof.text != "Y":
        r = reader.read(rec)
        if r is None:
            move("Y", ws_eof)
        else:
            wrap_text()

    out.extend(display_line("LINES ", ws_lines))
    return bytes(out), {}
