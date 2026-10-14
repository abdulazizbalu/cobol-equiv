from cobol_equiv.runtime import Storage, Alnum, Num, move
from cobol_equiv.runtime.files import RecordSequentialReader, RecordSequentialWriter


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    in_rec = Storage("INPUT-FILE", [Alnum("INPUT-RECORD", "X(80)")])
    out_rec = Storage("OUTPUT-FILE", [Alnum("OUTPUT-RECORD", "X(80)")])
    ws = Storage("WS", [
        Num("END-OF-FILE-FLAG", "9", value=0),
        Alnum("TEXT-LINE", "X(80)"),
    ])

    reader = RecordSequentialReader(input_files.get("input.txt", b""), 80)
    writer = RecordSequentialWriter()

    def read_input():
        r = reader.read(in_rec["INPUT-RECORD"])
        if r is None:
            move(1, ws["END-OF-FILE-FLAG"])
        else:
            move(in_rec["INPUT-RECORD"], ws["TEXT-LINE"])

    read_input()
    while int(ws["END-OF-FILE-FLAG"]) != 1:
        move(ws["TEXT-LINE"], out_rec["OUTPUT-RECORD"])
        writer.write(out_rec["OUTPUT-RECORD"])
        read_input()

    return b"", {"output.txt": writer.getvalue()}
