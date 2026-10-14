from cobol_equiv.runtime import Storage, Num, accept_line, ZEROS


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    ws = Storage("WS", [
        Num("CURRENT", "9(9)"),
    ])
    current_ref = ws["CURRENT"]

    data = stdin
    lines = data.split(b"\n")
    if data.endswith(b"\n"):
        lines = lines[:-1]
    idx = 0

    SHIFT = 38
    average = 0  # scaled by 10^9
    amount = 0
    MOD_AVG = 10 ** 18
    MOD_AMT = 10 ** 9

    while True:
        if idx >= len(lines):
            break
        line = lines[idx]
        idx += 1
        if line.endswith(b"\r"):
            line = line[:-1]
        accept_line(line, current_ref)
        current = int(current_ref)
        if current == 99999:
            break
        amount = (amount + 1) % MOD_AMT
        if amount == 0:
            # division by zero: size error, target unchanged
            continue
        # term1: average(scale 9) * (amount - 1) -> scale 9, / amount -> scale 47
        num1 = average * (amount - 1)
        t1 = (abs(num1) * 10 ** SHIFT) // amount
        if num1 < 0:
            t1 = -t1
        # term2: current(scale 0) / amount -> scale 38
        t2 = (current * 10 ** SHIFT) // amount
        # align to scale 47
        total = t1 + t2 * 10 ** 9
        # store into scale 9, truncate
        if total >= 0:
            v = total // 10 ** 38
        else:
            v = -((-total) // 10 ** 38)
        v = abs(v) % MOD_AVG
        average = v

    ip = average // 10 ** 9
    fp = average % 10 ** 9
    out = str(ip).rjust(9) + "." + str(fp).zfill(9)
    return (out + "\n").encode("latin-1"), {}
