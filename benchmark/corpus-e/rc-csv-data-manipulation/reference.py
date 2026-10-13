"""Reference translation of the Rosetta Code "CSV data manipulation" solution
csv-data-manipulation.cob."""

from cobol_equiv.runtime import Alnum, Edited, Num, Storage, compute, dec, move, string, unstring
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def _trim(b: bytes) -> bytes:
    return b.strip(b" ")


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("COL1", "9(5)"), Num("COL2", "9(5)"), Num("COL3", "9(5)"),
                        Num("COL4", "9(5)"), Num("COL5", "9(5)"), Edited("CSV-SUM", "ZZZ9")])
    io = Storage("IO", [Alnum("CSV-RECORD", "X(64)"), Alnum("OUT-LINE", "X(80)")])
    io.area[:] = bytes(len(io.area))  # GnuCOBOL starts FD record areas as binary zeros
    reader = LineSequentialReader(input_files["csv.txt"], 64)
    writer = LineSequentialWriter()
    eof = False

    def read():
        nonlocal eof
        rec = reader.read()
        if rec is None:
            eof = True
        else:
            io["CSV-RECORD"].set_raw(rec)

    read()
    string([(_trim(io["CSV-RECORD"].raw), None), (",SUM", None)], io["OUT-LINE"])
    writer.write(io["OUT-LINE"])
    move(" ", io["OUT-LINE"])
    while not eof:
        read()
        if not eof:
            cols = [ws["COL%d" % i] for i in range(1, 6)]
            unstring(io["CSV-RECORD"], [","], cols)
            compute(ws["CSV-SUM"], sum((dec(c) for c in cols[1:]), dec(cols[0])))
            string([(_trim(io["CSV-RECORD"].raw), None), (",", None),
                    (_trim(ws["CSV-SUM"].raw), None)], io["OUT-LINE"])
            writer.write(io["OUT-LINE"])
            move(" ", io["OUT-LINE"])
    return b"", {"new.csv.txt": writer.getvalue()}
