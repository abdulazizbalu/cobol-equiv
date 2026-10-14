from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited, move, compute, dec, string, unstring,
    SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def _trim(ref):
    data = ref.raw
    s = data.strip(b" ")
    return s


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    csv_rec = Storage("CSV-Record-S", [
        Group("CSV-Record", [Alnum("Field1", "X(64)")]),
    ], area=bytearray(64))
    out_rec = Storage("Out-Line-S", [
        Alnum("Out-Line", "X(80)"),
    ], area=bytearray(80))
    ws = Storage("WS", [
        Alnum("Eof", "X", value="F"),
        Group("CSV-Data", [
            Num("CSV-Col1", "9(5)"),
            Num("CSV-Col2", "9(5)"),
            Num("CSV-Col3", "9(5)"),
            Num("CSV-Col4", "9(5)"),
            Num("CSV-Col5", "9(5)"),
        ]),
        Edited("CSV-Sum", "ZZZ9"),
        Alnum("CSV-Sum-Alpha", "X(4)", redefines="CSV-Sum"),
    ])

    rec = csv_rec["CSV-Record"]
    out_line = out_rec["Out-Line"]
    eof = ws["Eof"]

    reader = LineSequentialReader(input_files.get("csv.txt", b""), 64)
    writer = LineSequentialWriter()

    def read_a_record():
        r = reader.read(rec)
        if r is None:
            move("T", eof)

    def build_header():
        string([(_trim(rec), None), (b",SUM", None)], out_line)
        writer.write(out_line)
        move(SPACES, out_line)

    def process_a_record():
        unstring(rec, [","], [ws["CSV-Col1"], ws["CSV-Col2"], ws["CSV-Col3"],
                              ws["CSV-Col4"], ws["CSV-Col5"]])
        compute(ws["CSV-Sum"],
                dec(ws["CSV-Col1"]) + dec(ws["CSV-Col2"]) + dec(ws["CSV-Col3"])
                + dec(ws["CSV-Col4"]) + dec(ws["CSV-Col5"]))
        string([(_trim(rec), None), (b",", None),
                (_trim(ws["CSV-Sum-Alpha"]), None)], out_line)
        writer.write(out_line)
        move(SPACES, out_line)

    read_a_record()
    build_header()
    while eof.raw != b"T":
        read_a_record()
        if eof.raw != b"T":
            process_a_record()

    return b"", {"new.csv.txt": writer.getvalue()}
