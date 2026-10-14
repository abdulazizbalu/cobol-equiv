from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, compute, dec, string, unstring, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader, LineSequentialWriter


def _trim(raw: bytes) -> str:
    # FUNCTION TRIM: remove leading and trailing spaces
    return raw.strip(b" ").decode("latin-1")


def _string_into(parts, into):
    real = [(p, None) for p in parts if p != ""]
    if real:
        string(real, into)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
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
        Group("CSV-Sum-G", [
            Num("CSV-Sum-Dummy", "9(4)"),
        ]),
    ])
    # CSV-Sum (ZZZ9) with REDEFINES as X(4): separate storage
    from cobol_equiv.runtime import Edited
    sum_st = Storage("SUM", [
        Edited("CSV-Sum", "ZZZ9"),
        Alnum("CSV-Sum-Alpha", "X(4)", redefines="CSV-Sum"),
    ])

    record = csv_rec["CSV-Record"]
    out_line = out_rec["Out-Line"]
    eof = ws["Eof"]

    reader = LineSequentialReader(input_files.get("csv.txt", b""), 64)
    writer = LineSequentialWriter()

    def read_a_record():
        r = reader.read(record)
        if r is None:
            move("T", eof)

    def build_header():
        _string_into([_trim(record.raw), ",SUM"], out_line)
        writer.write(out_line)
        move(SPACES, out_line)

    def process_a_record():
        unstring(record, [","], [
            ws["CSV-Col1"], ws["CSV-Col2"], ws["CSV-Col3"],
            ws["CSV-Col4"], ws["CSV-Col5"],
        ])
        compute(sum_st["CSV-Sum"],
                dec(ws["CSV-Col1"]) + dec(ws["CSV-Col2"]) + dec(ws["CSV-Col3"])
                + dec(ws["CSV-Col4"]) + dec(ws["CSV-Col5"]))
        _string_into([_trim(record.raw), ",", _trim(sum_st["CSV-Sum-Alpha"].raw)],
                     out_line)
        writer.write(out_line)
        move(SPACES, out_line)

    read_a_record()
    build_header()
    while eof.raw != b"T":
        read_a_record()
        if eof.raw != b"T":
            process_a_record()

    return b"", {"new.csv.txt": writer.getvalue()}
