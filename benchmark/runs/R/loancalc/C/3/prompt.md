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
input_files = {'LOANS.DAT': b'L0000000000000000000000\n'}
expected stdout = b'L00000 ERROR TERM ZERO\nLOANS 001 ERRORS 001\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'LOANS.DAT': b'L5803600007816299999122\n'}
expected stdout = b'L58036        $65.14      6,761.50 116        65.13        0.00\nLOANS 001 ERRORS 000\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. LOANCALC.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOAN-FILE ASSIGN TO "LOANS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD LOAN-FILE.
       01 LOAN-REC.
          05 LN-ID          PIC X(6).
          05 LN-PRINCIPAL   PIC 9(7)V99.
          05 LN-RATE        PIC 99V999.
          05 LN-TERM        PIC 9(3).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-MRATE          PIC 9V9(8).
       01 WS-FACTOR         PIC 9(9)V9(10).
       01 WS-PAYMENT        PIC 9(7)V99.
       01 WS-BALANCE        PIC S9(7)V99.
       01 WS-INTEREST       PIC 9(7)V99.
       01 WS-PRINC-PART     PIC S9(7)V99.
       01 WS-TOTAL-INT      PIC 9(8)V99.
       01 WS-MONTH          PIC 9(3).
       01 WS-LOANS          PIC 9(3) VALUE 0.
       01 WS-ERRORS         PIC 9(3) VALUE 0.
       01 OUT-LINE.
          05 OL-ID          PIC X(6).
          05 FILLER         PIC X VALUE SPACE.
          05 OL-PAYMENT     PIC $$,$$$,$$9.99.
          05 FILLER         PIC X VALUE SPACE.
          05 OL-TOTAL-INT   PIC ZZ,ZZZ,ZZ9.99.
          05 FILLER         PIC X VALUE SPACE.
          05 OL-MONTHS      PIC ZZ9.
          05 FILLER         PIC X VALUE SPACE.
          05 OL-FIRST-INT   PIC Z,ZZZ,ZZ9.99.
          05 FILLER         PIC X VALUE SPACE.
          05 OL-RESIDUAL    PIC -(7)9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT LOAN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ LOAN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PROCESS-LOAN
               END-READ
           END-PERFORM
           CLOSE LOAN-FILE
           DISPLAY "LOANS " WS-LOANS " ERRORS " WS-ERRORS
           STOP RUN.

       PROCESS-LOAN.
           ADD 1 TO WS-LOANS
           IF LN-TERM = 0
               DISPLAY LN-ID " ERROR TERM ZERO"
               ADD 1 TO WS-ERRORS
               EXIT PARAGRAPH
           END-IF
           COMPUTE WS-MRATE ROUNDED = LN-RATE / 1200
           IF WS-MRATE = 0
               COMPUTE WS-PAYMENT ROUNDED = LN-PRINCIPAL / LN-TERM
           ELSE
               MOVE 1 TO WS-FACTOR
               PERFORM LN-TERM TIMES
                   COMPUTE WS-FACTOR ROUNDED =
                       WS-FACTOR * (1 + WS-MRATE)
                       ON SIZE ERROR
                           DISPLAY LN-ID " ERROR FACTOR OVERFLOW"
                           ADD 1 TO WS-ERRORS
                           EXIT PARAGRAPH
                   END-COMPUTE
               END-PERFORM
               COMPUTE WS-PAYMENT ROUNDED =
                   LN-PRINCIPAL * WS-MRATE * WS-FACTOR / (WS-FACTOR - 1)
                   ON SIZE ERROR
                       DISPLAY LN-ID " ERROR PAYMENT OVERFLOW"
                       ADD 1 TO WS-ERRORS
                       EXIT PARAGRAPH
               END-COMPUTE
           END-IF
           MOVE LN-PRINCIPAL TO WS-BALANCE
           MOVE 0 TO WS-TOTAL-INT WS-MONTH OL-FIRST-INT
           PERFORM UNTIL WS-BALANCE <= 0 OR WS-MONTH >= LN-TERM
               ADD 1 TO WS-MONTH
               COMPUTE WS-INTEREST ROUNDED = WS-BALANCE * WS-MRATE
               IF WS-MONTH = 1
                   MOVE WS-INTEREST TO OL-FIRST-INT
               END-IF
               COMPUTE WS-PRINC-PART = WS-PAYMENT - WS-INTEREST
               IF WS-PRINC-PART > WS-BALANCE OR WS-MONTH = LN-TERM
                   MOVE WS-BALANCE TO WS-PRINC-PART
               END-IF
               ADD WS-INTEREST TO WS-TOTAL-INT
               SUBTRACT WS-PRINC-PART FROM WS-BALANCE
           END-PERFORM
           MOVE LN-ID TO OL-ID
           MOVE WS-PAYMENT TO OL-PAYMENT
           MOVE WS-TOTAL-INT TO OL-TOTAL-INT
           MOVE WS-MONTH TO OL-MONTHS
           MOVE WS-BALANCE TO OL-RESIDUAL
           DISPLAY OUT-LINE.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
