from cobol_equiv.runtime import (
    Storage, Alnum, Stdin, move, inspect_converting, display_line,
)

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"


def _lower(b: bytes) -> bytes:
    return bytes((c + 32) if 65 <= c <= 90 else c for c in b)


def _upper(b: bytes) -> bytes:
    return bytes((c - 32) if 97 <= c <= 122 else c for c in b)


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Alnum("EXAMPLE", "X(9)"),
        Alnum("RESULT", "X(9)"),
    ])
    example = ws["EXAMPLE"]
    result = ws["RESULT"]
    inp = Stdin(stdin)
    out = bytearray()

    inp.accept(example)
    out += display_line("Example: ", example)

    out += display_line("Lower-case: ", _lower(example.raw))
    out += display_line("Upper-case: ", _upper(example.raw))

    move(example, result)
    inspect_converting(result, UPPER, LOWER)
    out += display_line("Lower-case: ", result)

    move(example, result)
    inspect_converting(result, LOWER, UPPER)
    out += display_line("Upper-case: ", result)

    return bytes(out), {}
