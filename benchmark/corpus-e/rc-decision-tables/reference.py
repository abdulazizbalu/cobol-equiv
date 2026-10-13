"""Reference translation of the Rosetta Code "Decision tables" solution decision-tables.cob."""

from cobol_equiv.runtime import Stdin

ACTIONS = {
    b"YYY": [b"Check the printer-computer cable", b"Ensure printer software is installed",
             b"Check/replace ink"],
    b"YYN": [b"Check/replace ink", b"Check for paper jam"],
    b"YNY": [b"Check the power cable", b"Check the printer-computer cable",
             b"Ensure printer software is installed"],
    b"YNN": [b"Check for paper jam"],
    b"NYY": [b"Ensure printer software is installed", b"Check/replace ink"],
    b"NYN": [b"Check/replace ink"],
    b"NNY": [b"Ensure printer software is installed"],
    b"NNN": [b"no action found"],
}


def _first(line: bytes) -> bytes:
    return (line + b" ")[:1]  # ACCEPT into PIC X


def main(stdin: bytes, input_files: dict) -> tuple:
    inp = Stdin(stdin)
    out = [b" "]
    out.append(b"The printer does not print (Y or N) ")
    a = _first(inp.read_line())
    out[-1] += b"A red light is flashing (Y or N) "
    b = _first(inp.read_line())
    out[-1] += b"The printer is unrecognized (Y or N) "
    c = _first(inp.read_line())
    cond = bytes(x - 32 if 0x61 <= x <= 0x7A else x for x in a + b + c)
    out[-1] += b" "  # DISPLAY SPACE after the last prompt (no advancing)
    acts = ACTIONS.get(cond)
    if acts is None:
        out.append(b"invalid input: " + cond[0:1] + b" " + cond[1:2] + b" " + cond[2:3])
    else:
        out += acts
    out.append(b" ")
    return b"".join(line + b"\n" for line in out), {}
