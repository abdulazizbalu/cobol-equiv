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
input_files = {'TXN.DAT': b'A000A000000p\n'}
expected stdout = b'A000 OK    A +00000.00 +00000.00 +0000\nCOUNT 0001 ERRORS 0000\nFINAL +00000.00 +00000.00 +0000\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'TXN.DAT': b'A100A000000p\n'}
expected stdout = b'A100 OK    A +00000.00 +00000.00 +0000\nCOUNT 0001 ERRORS 0000\nFINAL +00000.00 +00000.00 +0000\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SIZEERR.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TXN-FILE ASSIGN TO "TXN.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD TXN-FILE.
       01 TXN-REC.
          05 TX-ACCT        PIC X(4).
          05 TX-OP          PIC X.
          05 TX-AMOUNT      PIC S9(5)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-ACC            PIC S9(5)V99 COMP-3 VALUE 0.
       01 WS-RAW            PIC S9(5)V99 VALUE 0.
       01 WS-BIN            PIC S9(4) COMP VALUE 0.
       01 WS-QUOT           PIC S9(3)V9 VALUE 0.
       01 WS-REM            PIC S9(5)V99 VALUE 0.
       01 WS-ERRORS         PIC 9(4) VALUE 0.
       01 WS-COUNT          PIC 9(4) VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT TXN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ TXN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM APPLY-TXN
               END-READ
           END-PERFORM
           CLOSE TXN-FILE
           DISPLAY "COUNT " WS-COUNT " ERRORS " WS-ERRORS
           DISPLAY "FINAL " WS-ACC " " WS-RAW " " WS-BIN
           STOP RUN.

       APPLY-TXN.
           ADD 1 TO WS-COUNT
           EVALUATE TX-OP
               WHEN "A"
                   ADD TX-AMOUNT TO WS-ACC
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-ADD
                   ADD TX-AMOUNT TO WS-RAW WS-BIN
               WHEN "S"
                   SUBTRACT TX-AMOUNT FROM WS-ACC
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-SUBTRACT
                   SUBTRACT TX-AMOUNT FROM WS-RAW WS-BIN
               WHEN "M"
                   MULTIPLY TX-AMOUNT BY WS-ACC ROUNDED
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-MULTIPLY
                   MULTIPLY TX-AMOUNT BY WS-RAW ROUNDED WS-BIN
               WHEN "D"
                   DIVIDE TX-AMOUNT INTO WS-ACC ROUNDED
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-DIVIDE
                   DIVIDE TX-AMOUNT INTO WS-RAW ROUNDED
               WHEN "Q"
                   DIVIDE WS-ACC BY TX-AMOUNT
                       GIVING WS-QUOT REMAINDER WS-REM
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR
                           DISPLAY TX-ACCT " Q " WS-QUOT " R " WS-REM
                   END-DIVIDE
               WHEN OTHER
                   DISPLAY TX-ACCT " BAD OPERATION " TX-OP
           END-EVALUATE.

       SHOW-OK.
           DISPLAY TX-ACCT " OK    " TX-OP " " WS-ACC " " WS-RAW " "
               WS-BIN.

       SHOW-ERROR.
           ADD 1 TO WS-ERRORS
           DISPLAY TX-ACCT " ERROR " TX-OP " " WS-ACC " " WS-RAW " "
               WS-BIN.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
