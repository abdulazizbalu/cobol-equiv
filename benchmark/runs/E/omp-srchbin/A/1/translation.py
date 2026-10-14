from cobol_equiv.runtime import Storage, Alnum, display_line
from cobol_equiv.runtime.files import RecordSequentialReader


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("ACCT-REC", [Alnum("ACCT-FIELDS", "X(170)")])
    reader = RecordSequentialReader(input_files.get("ACCTREC", b""), 170)

    table_max = 45
    # Unloaded entries: ACCT-NO initialised to spaces
    keys = [b" " * 8 for _ in range(table_max)]

    eof = False

    def read_record():
        nonlocal eof
        r = reader.read(rec["ACCT-FIELDS"])
        if r is None:
            eof = True

    read_record()
    table_var = 1
    while not (table_var == table_max or eof):
        keys[table_var - 1] = bytes(rec["ACCT-FIELDS"].raw[:8])
        read_record()
        table_var += 1

    # SEARCH ALL (GnuCOBOL binary search)
    target = b"18011809"
    head = 0
    tail = table_max + 1
    while True:
        if head >= tail - 1:
            out += display_line("Not Found")
            break
        idx = (head + tail) // 2
        key = keys[idx - 1]
        if key == target:
            out += display_line("User with Acct No 18011809 is found!")
            break
        if key < target:
            head = idx
        else:
            tail = idx

    return bytes(out), {}
