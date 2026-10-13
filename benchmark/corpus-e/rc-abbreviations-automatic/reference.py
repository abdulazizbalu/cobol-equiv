"""Reference translation of the Rosetta Code "Abbreviations, automatic"
solution abbreviations-automatic.cob."""

from cobol_equiv.runtime.files import LineSequentialReader


def _unstring_space(line: bytes, ptr: int):
    """UNSTRING line DELIMITED BY SPACE INTO CURDAY WITH POINTER ptr.
    Returns (field or None when the pointer is out of range, new ptr)."""
    if ptr < 1 or ptr > len(line):
        return None, ptr
    i = ptr - 1
    j = line.find(b" ", i)
    if j < 0:
        return line[i:], len(line) + 1
    return line[i:j], j + 2


def main(stdin: bytes, input_files: dict) -> tuple:
    reader = LineSequentialReader(input_files["days-of-week.txt"], 200)
    out = bytearray()
    line_num = 1
    largest = 0  # LARGESTCHARAMT, never reset
    curday = b" " * 50
    while True:
        dow = reader.read()
        if dow is None:
            break
        if dow == b" " * 200:
            out += b" \n"  # DISPLAY "" prints one space
        else:
            endo2 = 0
            charamt = 0
            abbr = [b" " * 50] * 7
            while endo2 <= 0:
                ptr = 1
                daynum = 1
                restart = 0
                charamt += 1
                abbr = [b" " * 50] * 7
                for _ in range(7):
                    field, ptr = _unstring_space(dow, ptr)
                    if field is not None:
                        curday = field[:50].ljust(50)
                    tmp1 = 50 - curday.count(b" ")
                    if tmp1 > largest:
                        largest = tmp1 % 1000
                    if curday == b" " * 50:
                        endo2 = 3
                    curabbr = curday[:charamt].ljust(50)
                    if curabbr in abbr:
                        restart = 1
                    abbr[daynum - 1] = curabbr
                    daynum += 1
                if restart == 0:
                    endo2 = 1
                if charamt > largest:
                    endo2 = 2
            out += b"Line %03d: " % (line_num % 1000)
            if endo2 == 3:
                out += b"Error: not enough days\n"
            elif endo2 == 2:
                out += b"Error: identical days\n"
            else:
                out += b"%03d: " % charamt
                for t in range(7):
                    a = abbr[t]
                    n = 50 - (len(a) - len(a.rstrip(b" ")))
                    out += a[:n] + b"."
                    out += b" " if t < 6 else b"\n"
        line_num += 1
    return bytes(out), {}
