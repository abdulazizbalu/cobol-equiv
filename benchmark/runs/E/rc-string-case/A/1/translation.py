from cobol_equiv.runtime import (
    Storage, Alnum, move, inspect_converting, display_line, Stdin,
)

_UP = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LO = b"abcdefghijklmnopqrstuvwxyz"
_TO_LOWER = bytes.maketrans(_UP, _LO)
_TO_UPPER = bytes.maketrans(_LO, _UP)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Alnum("EXAMPLE", "X(9)"),
        Alnum("RESULT", "X(9)"),
    ])
    example = ws["EXAMPLE"]
    result = ws["RESULT"]
    out = bytearray()
    inp = Stdin(stdin)

    inp.accept(example)
    out += display_line("Example: ", example)

    out += display_line("Lower-case: ", bytes(example.raw).translate(_TO_LOWER))
    out += display_line("Upper-case: ", bytes(example.raw).translate(_TO_UPPER))

    move(example, result)
    inspect_converting(result, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
    out += display_line("Lower-case: ", result)

    move(example, result)
    inspect_converting(result, "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    out += display_line("Upper-case: ", result)

    return bytes(out), {}
