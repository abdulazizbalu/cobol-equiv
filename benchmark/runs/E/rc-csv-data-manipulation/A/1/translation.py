from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, Edited,
    move, compute, dec, string, unstring, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def _trim(raw: bytes) -> bytes:
    # FUNCTION TRIM removes leading and trailing spaces only
    return raw.strip(b" ")


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    # File record areas start as binary zeros in GnuCOBOL
    csv_rec = Storage("CSV-FILE", [
        Group("CSV-Record", [Alnum("Field1", "X(64)")]),
    ], area=bytearray(64))
    out_rec = Storage("OUT-FILE", [
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

    csv_record = csv_rec["CSV-Record"]
    out_line = out_rec["Out-Line"]
    eof = ws["Eof"]

    reader = LineSequentialReader(input_files.get("csv.txt", b""), 64)
    writer = LineSequentialWriter()

    def read_a_record():
        r = reader.read(csv_record)
        if r is None:
            move("T", eof)

    def build_header():
        string([(_trim(csv_record.raw), None), (",SUM", None)], out_line)
        writer.write(out_line)
        move(SPACES, out_line)

    def process_a_record():
        unstring(csv_record, [","], [
            ws["CSV-Col1"], ws["CSV-Col2"], ws["CSV-Col3"],
            ws["CSV-Col4"], ws["CSV-Col5"],
        ])
        compute(ws["CSV-Sum"],
                dec(ws["CSV-Col1"]) + dec(ws["CSV-Col2"]) + dec(ws["CSV-Col3"])
                + dec(ws["CSV-Col4"]) + dec(ws["CSV-Col5"]))
        parts = [(_trim(csv_record.raw), None), (",", None)]
        t = _trim(ws["CSV-Sum-Alpha"].raw)
        if t:
            parts.append((t, None))
        string(parts, out_line)
        writer.write(out_line)
        move(SPACES, out_line)

    read_a_record()
    build_header()
    while eof.text != "T":
        read_a_record()
        if eof.text != "T":
            process_a_record()

    return b"", {"new.csv.txt": writer.getvalue()}
