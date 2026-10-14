Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

Use only the Python standard library. The module runs in an interpreter
that has no other packages.

## IO contract
The Python module must define

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]

- stdin: everything the program reads with ACCEPT (one ACCEPT reads one line).
- input_files: for every file the program reads, the name in its ASSIGN
  clause mapped to the full content of the file. LINE SEQUENTIAL files are
  lines that end with "\n"; SEQUENTIAL files are fixed-length records
  without separators.
- The return value is all bytes the program writes to standard output, and
  a dict that maps the ASSIGN name of every file the program opens for
  output to the full content of that file.
- The module must not read the clock, random sources, the network or the
  file system, and must not start processes. It runs on Python 3.12.

## Examples
These are inputs and the exact outputs of the COBOL program.
### Example 1
stdin = b''
input_files = {'sedol.txt': b'000000\n'}
expected stdout = b'0000000\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'sedol.txt': b'1Q9M50\nL8VWZ0\nWBK0T9\n'}
expected stdout = b'1Q9M503\nL8VWZ05\nWBK0T97\n'
expected output_files = {}

## COBOL program
```cobol
       >>SOURCE FREE
IDENTIFICATION DIVISION.
PROGRAM-ID. sedol.

ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT sedol-file ASSIGN "sedol.txt"
        ORGANIZATION LINE SEQUENTIAL
        FILE STATUS sedol-file-status.

DATA DIVISION.
FILE SECTION.
FD  sedol-file.
01  sedol                               PIC X(6).

WORKING-STORAGE SECTION.
01  sedol-file-status                   PIC XX.
    88  sedol-file-ok                   VALUE "00".

01  digit-num                           PIC 9 COMP.

01  digit-weights-area                  VALUE "1317391".
    03  digit-weights                   PIC 9 OCCURS 7 TIMES.

01  weighted-sum-parts-area.
    03  weighted-sum-parts              PIC 9(3) COMP OCCURS 6 TIMES.

01  weighted-sum                        PIC 9(3) COMP.

01  check-digit                         PIC 9.

PROCEDURE DIVISION.
    OPEN INPUT sedol-file
    PERFORM UNTIL NOT sedol-file-ok
        READ sedol-file
            AT END
                EXIT PERFORM
        END-READ

        MOVE FUNCTION UPPER-CASE(sedol) TO sedol

        PERFORM VARYING digit-num FROM 1 BY 1 UNTIL digit-num > 6
            EVALUATE TRUE
                WHEN sedol (digit-num:1) IS ALPHABETIC-UPPER
                    IF sedol (digit-num:1) = "A" OR "E" OR "I" OR "O" OR "U"
                        DISPLAY "Invalid SEDOL: " sedol
                        EXIT PERFORM CYCLE
                    END-IF

                    COMPUTE weighted-sum-parts (digit-num) =
                        (FUNCTION ORD(sedol (digit-num:1)) - FUNCTION ORD("A")
                        + 10) * digit-weights (digit-num)

                WHEN sedol (digit-num:1) IS NUMERIC
                    MULTIPLY FUNCTION NUMVAL(sedol (digit-num:1))
                        BY digit-weights (digit-num)
                        GIVING weighted-sum-parts (digit-num)

                WHEN OTHER
                    DISPLAY "Invalid SEDOL: " sedol
                    EXIT PERFORM CYCLE
            END-EVALUATE
        END-PERFORM

        INITIALIZE weighted-sum
        PERFORM VARYING digit-num FROM 1 BY 1 UNTIL digit-num > 6
            ADD weighted-sum-parts (digit-num) TO weighted-sum
        END-PERFORM

        COMPUTE check-digit =
            FUNCTION MOD(10 - FUNCTION MOD(weighted-sum, 10), 10)

        DISPLAY sedol check-digit
    END-PERFORM

    CLOSE sedol-file
    .
END PROGRAM sedol.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
