"""Reference translation of the Rosetta Code "Input loop" solution input-loop.cob."""

from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    reader = LineSequentialReader(stdin, 80)
    out = bytearray()
    while (rec := reader.read()) is not None:
        out += rec + b"\n"
    return bytes(out), {}
