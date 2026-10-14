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
input_files = {'CARDS.DAT': b'\n'}
expected stdout = b'SHORT [                ]\nVALID 000 INVALID 000 REJECTED 001\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'CARDS.DAT': b'><q+\n'}
expected stdout = b'NOT NUMERIC [><q+]\nVALID 000 INVALID 000 REJECTED 001\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. LUHN.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CARD-FILE ASSIGN TO "CARDS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CARD-FILE.
       01 CARD-REC.
          05 CD-NUMBER      PIC X(16).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-LEN            PIC 99.
       01 WS-POS            PIC 99.
       01 WS-DIGIT          PIC 9.
       01 WS-DOUBLE         PIC 99.
       01 WS-SUM            PIC 9(3).
       01 WS-QUOT           PIC 9(3).
       01 WS-REM            PIC 9.
       01 WS-CHECK          PIC 9.
       01 WS-ODD            PIC X.
       01 WS-VALID          PIC 9(3) VALUE 0.
       01 WS-INVALID        PIC 9(3) VALUE 0.
       01 WS-REJECTED       PIC 9(3) VALUE 0.
       01 WS-FIXED          PIC X(16).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CARD-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CARD-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM CHECK-CARD
               END-READ
           END-PERFORM
           CLOSE CARD-FILE
           DISPLAY "VALID " WS-VALID " INVALID " WS-INVALID
               " REJECTED " WS-REJECTED
           STOP RUN.

       CHECK-CARD.
           MOVE 0 TO WS-LEN
           INSPECT CD-NUMBER TALLYING WS-LEN
               FOR CHARACTERS BEFORE INITIAL SPACE
           IF WS-LEN < 2
               ADD 1 TO WS-REJECTED
               DISPLAY "SHORT [" CD-NUMBER "]"
           ELSE
               IF CD-NUMBER (1:WS-LEN) IS NOT NUMERIC
                   ADD 1 TO WS-REJECTED
                   DISPLAY "NOT NUMERIC [" CD-NUMBER (1:WS-LEN) "]"
               ELSE
                   PERFORM LUHN-SUM
                   PERFORM REPORT-CARD
               END-IF
           END-IF.

       LUHN-SUM.
           MOVE 0 TO WS-SUM
           MOVE "N" TO WS-ODD
           PERFORM VARYING WS-POS FROM WS-LEN BY -1 UNTIL WS-POS < 2
               MOVE CD-NUMBER (WS-POS - 1:1) TO WS-DIGIT
               IF WS-ODD = "N"
                   MULTIPLY WS-DIGIT BY 2 GIVING WS-DOUBLE
                   IF WS-DOUBLE > 9
                       SUBTRACT 9 FROM WS-DOUBLE
                   END-IF
                   ADD WS-DOUBLE TO WS-SUM
                   MOVE "Y" TO WS-ODD
               ELSE
                   ADD WS-DIGIT TO WS-SUM
                   MOVE "N" TO WS-ODD
               END-IF
           END-PERFORM
           DIVIDE WS-SUM BY 10 GIVING WS-QUOT REMAINDER WS-REM
           IF WS-REM = 0
               MOVE 0 TO WS-CHECK
           ELSE
               COMPUTE WS-CHECK = 10 - WS-REM
           END-IF.

       REPORT-CARD.
           MOVE CD-NUMBER (WS-LEN:1) TO WS-DIGIT
           IF WS-DIGIT = WS-CHECK
               ADD 1 TO WS-VALID
               DISPLAY "VALID " CD-NUMBER (1:WS-LEN)
           ELSE
               ADD 1 TO WS-INVALID
               MOVE CD-NUMBER TO WS-FIXED
               MOVE WS-CHECK TO WS-FIXED (WS-LEN:1)
               DISPLAY "INVALID " CD-NUMBER (1:WS-LEN) " SUM " WS-SUM
                   " EXPECTED " WS-FIXED
           END-IF.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
