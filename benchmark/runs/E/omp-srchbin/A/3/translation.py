from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import RecordSequentialReader

RECORD_SIZE = 170
OCCURS = 45
TABLE_MAX = 45
KEY_VALUE = b"18011809"


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("ACCT-REC", [Alnum("ACCT-FIELDS", "X(170)")])
    reader = RecordSequentialReader(input_files.get("ACCTREC", b""), RECORD_SIZE)

    # Initial table state: ACCT-NO spaces (other fields irrelevant for search)
    table = [b" " * 8 for _ in range(OCCURS)]

    eof = False

    def read_record():
        nonlocal eof
        r = reader.read(rec["ACCT-FIELDS"])
        if r is None:
            eof = True

    # LOAD-TABLES
    read_record()
    table_var = 1
    while not (table_var == TABLE_MAX or eof):
        raw = rec["ACCT-FIELDS"].raw
        table[table_var - 1] = bytes(raw[:8])
        read_record()
        table_var += 1

    # SEARCH ALL (GnuCOBOL binary search)
    head = 0
    tail = OCCURS + 1
    while True:
        if head >= tail - 1:
            out += b"Not Found\n"
            break
        idx = (head + tail) // 2
        key = table[idx - 1]
        if key == KEY_VALUE:
            out += b"User with Acct No 18011809 is found!\n"
            break
        if key < KEY_VALUE:
            head = idx
        else:
            tail = idx

    return bytes(out), {}
