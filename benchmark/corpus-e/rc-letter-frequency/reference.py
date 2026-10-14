"""Reference translation of the Rosetta Code "Letter frequency" solution letter-frequency.cob."""

from cobol_equiv.runtime import Edited, Storage, move
from cobol_equiv.runtime.files import LineSequentialReader

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def main(stdin: bytes, input_files: dict) -> tuple:
    reader = LineSequentialReader(input_files["File.txt"], 80)
    record = bytes(80)  # FD record area starts as binary zeros
    counts = [0] * 26
    eof = False
    while not eof:
        rec = reader.read()
        if rec is None:
            eof = True  # the INSPECTs below still run on the unchanged record area
        else:
            record = rec
        upper = bytes(c - 32 if 0x61 <= c <= 0x7A else c for c in record)
        for i, ch in enumerate(LETTERS):
            counts[i] = (counts[i] + upper.count(ch.encode())) % 100000  # PIC 9(5)
    disp = Storage("DISP", [Edited(f"{ch}-CNT", "ZZZZ9") for ch in LETTERS])
    for i, ch in enumerate(LETTERS):
        move(counts[i], disp[f"{ch}-CNT"])
    out = bytearray(b"Letter Frequency Distribution\n-----------------------------\n")
    for i in range(13):
        a, b = LETTERS[i], LETTERS[i + 13]
        out += (a.encode() + b" : " + disp[f"{a}-CNT"].raw + b"          " + b.encode() + b" : "
                + disp[f"{b}-CNT"].raw + b"\n")
    return bytes(out), {}
