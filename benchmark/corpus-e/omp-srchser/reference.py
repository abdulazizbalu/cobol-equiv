"""Reference translation of benchmark/corpus-e/omp-srchser/program.cob."""


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files["ACCTREC"]
    size = 170
    recs = [data[i:i + size] for i in range(0, len(data) - len(data) % size, size)]
    # PERFORM VARYING TABLE-VAR FROM 1 UNTIL TABLE-VAR = 45 OR END-OF-FILE
    # loads at most 44 entries; the rest of the table keeps spaces / zeros.
    table = recs[:44]
    for entry in table:
        if entry[18:38] == b"ROOSEVELT".ljust(20):
            return b"Roosevelt is found!\n", {}
    return b"Not Found\n", {}
