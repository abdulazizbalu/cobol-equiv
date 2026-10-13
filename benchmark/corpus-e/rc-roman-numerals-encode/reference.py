"""Reference translation of the Rosetta Code "Roman numerals/Encode" solution
roman-numerals-encode.cob."""

from cobol_equiv.runtime import Num, Stdin, Storage, display_line

TABLE = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
         (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def main(stdin: bytes, input_files: dict) -> tuple:
    ws = Storage("WS", [Num("WS-NUMBER", "9(4)", value=0), Num("WS-SAVE-NUMBER", "9(4)")])
    inp = Stdin(stdin)
    out = bytearray()
    inp.accept(ws["WS-NUMBER"])
    while ws["WS-NUMBER"].value != 0:
        n = int(ws["WS-NUMBER"].value)
        save = ws["WS-NUMBER"].raw
        if 0 < n < 4000:
            roman = ""
            for value, chars in TABLE:
                while n >= value:
                    roman += chars
                    n -= value
            out += b"inp=" + save + b" roman=" + roman.encode().ljust(16) + b"\n"
        else:
            out += b"inp=" + save + b" invalid\n"
        inp.accept(ws["WS-NUMBER"])
    return bytes(out), {}
