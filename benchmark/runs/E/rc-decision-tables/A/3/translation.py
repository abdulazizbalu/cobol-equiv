from cobol_equiv.runtime import Storage, Group, Alnum, Stdin, display_line, SPACES


def _ascii_upper(b: bytes) -> bytes:
    return bytes((c - 32) if 97 <= c <= 122 else c for c in b)


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
    cond.set_raw(_ascii_upper(cond.raw))

    out += display_line(" ")

    key = (ws["NOTPRINTING"].raw, ws["FLASHING"].raw, ws["NOTRECOGNIZED"].raw)
    table = {
        (b"Y", b"Y", b"Y"): ["Check the printer-computer cable",
                             "Ensure printer software is installed",
                             "Check/replace ink"],
        (b"Y", b"Y", b"N"): ["Check/replace ink", "Check for paper jam"],
        (b"Y", b"N", b"Y"): ["Check the power cable",
                             "Check the printer-computer cable",
                             "Ensure printer software is installed"],
        (b"Y", b"N", b"N"): ["Check for paper jam"],
        (b"N", b"Y", b"Y"): ["Ensure printer software is installed",
                             "Check/replace ink"],
        (b"N", b"Y", b"N"): ["Check/replace ink"],
        (b"N", b"N", b"Y"): ["Ensure printer software is installed"],
        (b"N", b"N", b"N"): ["no action found"],
    }
    if key in table:
        for line in table[key]:
            out += display_line(line)
    else:
        out += display_line("invalid input: ", ws["NOTPRINTING"], " ",
                            ws["FLASHING"], " ", ws["NOTRECOGNIZED"])

    out += display_line(" ")
    return bytes(out), {}
