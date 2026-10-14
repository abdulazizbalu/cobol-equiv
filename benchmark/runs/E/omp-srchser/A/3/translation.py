from cobol_equiv.runtime import Storage, Alnum
from cobol_equiv.runtime.files import RecordSequentialReader

RECORD_SIZE = 170
TABLE_MAX = 45
# The table entry has the same layout as the 170-byte record:
# ACCT-NO X(8), ACCT-LIMIT and ACCT-BALANCE S9(7)V99 COMP-3 (5 bytes each),
# then LAST-NAME X(20).
LAST_NAME_OFFSET = 8 + 5 + 5
LAST_NAME_LEN = 20


def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    out = bytearray()

    rec = Storage("ACCT-REC", [Alnum("ACCT-FIELDS", "X(170)")])
    acct_fields = rec["ACCT-FIELDS"]

    reader = RecordSequentialReader(input_files.get("ACCTREC", b""), RECORD_SIZE)

    # The table is initialised to spaces. Unused entries never match "ROOSEVELT".
    table = [b" " * RECORD_SIZE for _ in range(TABLE_MAX)]

    end_of_file = False

    def read_record():
        nonlocal end_of_file
        r = reader.read(acct_fields)
        if r is None:
            end_of_file = True

    read_record()
    table_var = 1
    while not (table_var == TABLE_MAX or end_of_file):
        table[table_var - 1] = bytes(acct_fields.raw)
        read_record()
        table_var += 1

    target = b"ROOSEVELT".ljust(LAST_NAME_LEN, b" ")
    found = False
    for idx in range(TABLE_MAX):
        last_name = table[idx][LAST_NAME_OFFSET:LAST_NAME_OFFSET + LAST_NAME_LEN]
        if last_name == target:
            found = True
            break

    if found:
        out += b"Roosevelt is found!\n"
    else:
        out += b"Not Found\n"

    return bytes(out), {}
