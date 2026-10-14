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
input_files = {'LOANS.DAT': b'L00100000000000000000\n'}
expected stdout = b'L001 INVALID\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'LOANS.DAT': b'L00399999999800001235\n'}
expected stdout = b'L003 INVALID\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INTEREST.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOAN-FILE ASSIGN TO "LOANS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD LOAN-FILE.
       01 LOAN-REC.
          05 LN-ID          PIC X(4).
          05 LN-PRINCIPAL   PIC 9(7)V99.
          05 LN-RATE        PIC 99V999.
          05 LN-YEARS       PIC 99.
          05 LN-FREQ        PIC 9.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-PERIODS        PIC 99.
       01 WS-COUNT          PIC 9(4).
       01 WS-PERIOD-RATE    PIC 9V9(8).
       01 WS-FACTOR         PIC 9(3)V9(8).
       01 WS-SIMPLE         PIC S9(9)V99.
       01 WS-COMPOUND       PIC S9(9)V99.
       01 WS-MIXED          PIC S9(7)V9(4).
       01 WS-AVG            PIC S9(9)V99.
       01 WS-FLAG           PIC X.
       01 WS-OUT-1          PIC -(9)9.99.
       01 WS-OUT-2          PIC -(9)9.99.
       01 WS-OUT-3          PIC -(7)9.9(4).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT LOAN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ LOAN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM CALC-LOAN
               END-READ
           END-PERFORM
           CLOSE LOAN-FILE
           STOP RUN.

       CALC-LOAN.
           EVALUATE LN-FREQ
               WHEN 1 MOVE 1 TO WS-PERIODS
               WHEN 2 MOVE 2 TO WS-PERIODS
               WHEN 3 MOVE 4 TO WS-PERIODS
               WHEN 4 MOVE 12 TO WS-PERIODS
               WHEN OTHER MOVE 0 TO WS-PERIODS
           END-EVALUATE
           IF WS-PERIODS = 0 OR LN-YEARS = 0 OR LN-YEARS > 40
               DISPLAY LN-ID " INVALID"
           ELSE
               PERFORM CALC-VALUES
           END-IF.

       CALC-VALUES.
           MOVE "N" TO WS-FLAG
           COMPUTE WS-SIMPLE ROUNDED =
               LN-PRINCIPAL * LN-RATE / 100 * LN-YEARS
           COMPUTE WS-PERIOD-RATE = LN-RATE / 100 / WS-PERIODS
           MOVE 1 TO WS-FACTOR
           COMPUTE WS-COUNT = WS-PERIODS * LN-YEARS
           PERFORM WS-COUNT TIMES
               COMPUTE WS-FACTOR ROUNDED =
                   WS-FACTOR * (1 + WS-PERIOD-RATE)
                   ON SIZE ERROR MOVE "Y" TO WS-FLAG
               END-COMPUTE
           END-PERFORM
           COMPUTE WS-COMPOUND ROUNDED =
               LN-PRINCIPAL * WS-FACTOR - LN-PRINCIPAL
               ON SIZE ERROR MOVE "Y" TO WS-FLAG
           END-COMPUTE
           COMPUTE WS-MIXED =
               (LN-PRINCIPAL + LN-YEARS * 1000) / (LN-RATE + 1)
               - -LN-YEARS * 2.5 - WS-PERIODS / 3
           COMPUTE WS-AVG ROUNDED = (WS-SIMPLE + WS-COMPOUND) / 2
           MOVE WS-SIMPLE TO WS-OUT-1
           MOVE WS-COMPOUND TO WS-OUT-2
           MOVE WS-MIXED TO WS-OUT-3
           DISPLAY LN-ID " S" WS-OUT-1 " C" WS-OUT-2 " M" WS-OUT-3
               " F" WS-FACTOR " " WS-FLAG
           MOVE WS-AVG TO WS-OUT-1
           DISPLAY LN-ID " AVG" WS-OUT-1.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
