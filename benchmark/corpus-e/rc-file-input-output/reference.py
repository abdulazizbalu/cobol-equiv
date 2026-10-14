"""Reference translation of the Rosetta Code "File input/output" solution file-input-output-1.cob."""


def main(stdin: bytes, input_files: dict) -> tuple:
    data = input_files["input.txt"]
    out = b"".join(data[i:i + 80] for i in range(0, len(data) - len(data) % 80, 80))
    return b"", {"output.txt": out}
