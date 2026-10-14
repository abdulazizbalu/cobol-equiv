from decimal import Decimal

from cobol_equiv.runtime import (
    Storage, Num, Edited, move, display_line, accept_line,
)

SHIFT = 38


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("AVERAGE", "9(9)V9(9)", value=0),
        Num("AMOUNT", "9(9)", value=0),
        Num("CURRENT", "9(9)"),
        Edited("OUTPUT-VAL", "Z(8)9.9(9)"),
    ])
    out = bytearray()

    average = ws["AVERAGE"]
    amount = ws["AMOUNT"]
    current = ws["CURRENT"]
    output_val = ws["OUTPUT-VAL"]

    lines = stdin.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    idx = 0

    while True:
        if idx >= len(lines):
            break
        line = lines[idx]
        idx += 1
        if line.endswith(b"\r"):
            line = line[:-1]
        accept_line(line, current)
        cur = int(current)
        if cur == 99999:
            break
        amt = (int(amount) + 1) % (10 ** 9)
        move(amt, amount)
        if amt == 0:
            continue
        # AVERAGE as scaled integer (scale 9)
        avg_scaled = int(average.value * (10 ** 9))
        # AVERAGE * (AMOUNT - 1): scale 9
        p = avg_scaled * (amt - 1)
        # / AMOUNT: scale 9 + 38
        if p == 0:
            q1 = 0
        else:
            q1 = (p * 10 ** SHIFT) // amt
        s1 = 9 + SHIFT
        # CURRENT / AMOUNT: scale 38
        if cur == 0:
            q2 = 0
        else:
            q2 = (cur * 10 ** SHIFT) // amt
        s2 = SHIFT
        # add, aligned to scale s1
        total = q1 + q2 * 10 ** (s1 - s2)
        # truncate to scale 9
        res = total // 10 ** (s1 - 9)
        res %= 10 ** 18
        move(Decimal(res).scaleb(-9), average)

    move(average, output_val)
    out += display_line(output_val)
    return bytes(out), {}
