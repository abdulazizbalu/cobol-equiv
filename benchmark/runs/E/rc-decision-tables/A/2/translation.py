from cobol_equiv.runtime import Storage, Group, Alnum, Stdin, display_line


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Group("CONDITIONS", [
            Alnum("NOTPRINTING", "X"),
            Alnum("FLASHING", "X"),
            Alnum("NOTRECOGNIZED", "X"),
        ]),
    ])
    inp = Stdin(stdin)
    out = bytearray()

    out += display_line(" ")

    out += b"The printer does not print (Y or N) "
    inp.accept(ws["NOTPRINTING"])
    out += b"A red light is flashing (Y or N) "
    inp.accept(ws["FLASHING"])
    out += b"The printer is unrecognized (Y or N) "
    inp.accept(ws["NOTRECOGNIZED"])

    cond = ws["CONDITIONS"]
    cond.set_raw(bytes(cond.raw).upper())

    out += display_line(" ")

    key = bytes(cond.raw)
    if key == b"YYY":
        out += display_line("Check the printer-computer cable")
        out += display_line("Ensure printer software is installed")
        out += display_line("Check/replace ink")
    elif key == b"YYN":
        out += display_line("Check/replace ink")
        out += display_line("Check for paper jam")
    elif key == b"YNY":
        out += display_line("Check the power cable")
        out += display_line("Check the printer-computer cable")
        out += display_line("Ensure printer software is installed")
    elif key == b"YNN":
        out += display_line("Check for paper jam")
    elif key == b"NYY":
        out += display_line("Ensure printer software is installed")
        out += display_line("Check/replace ink")
    elif key == b"NYN":
        out += display_line("Check/replace ink")
    elif key == b"NNY":
        out += display_line("Ensure printer software is installed")
    elif key == b"NNN":
        out += display_line("no action found")
    else:
        out += display_line("invalid input: ", ws["NOTPRINTING"], " ",
                            ws["FLASHING"], " ", ws["NOTRECOGNIZED"])

    out += display_line(" ")
    return bytes(out), {}
