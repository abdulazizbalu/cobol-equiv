"""Reference translation of the Rosetta Code "Fixed length records" solution
fixed-length-records-1.cob."""


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files["infile.dat"]
    recs = [data[i:i + 80] for i in range(0, len(data) - len(data) % 80, 80)]
    rev = [r[::-1] for r in recs]
    out = b"".join(r.rstrip(b" ") + b"\n" for r in rev)  # DISPLAY TRIM(... TRAILING)
    return out, {"outfile.dat": b"".join(rev)}
