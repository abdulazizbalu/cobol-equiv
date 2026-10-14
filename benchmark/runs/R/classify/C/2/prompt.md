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
input_files = {'CUST.DAT': b'C000P00000005000q000\n'}
expected stdout = b'C000 CREDIT  YOUNG-P    2 MINOR \nCREDIT 001 DEFAULT 000 WATCH 000 NORMAL 000\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'CUST.DAT': b'C060F00100408159s548\nC323P06400000477s723\nC647I070003628801000\nC474B02500005000q589\n'}
expected stdout = b'C060 CREDIT  UNKNOWN    2 MINOR \nC323 CREDIT  PERSONAL   2 ADULT \nC647 NORMAL  PUBLIC     0 SENIOR\nC474 CREDIT  BUSINESS   3 ADULT \nCREDIT 003 DEFAULT 000 WATCH 000 NORMAL 001\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CLASSIFY.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUST-FILE ASSIGN TO "CUST.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CUST-FILE.
       01 CUST-REC.
          05 CU-ID          PIC X(4).
          05 CU-TYPE        PIC X.
          05 CU-AGE         PIC 9(3).
          05 CU-BALANCE     PIC S9(7)V99.
          05 CU-DAYS-LATE   PIC 9(3).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-CLASS          PIC X(7).
       01 WS-SEGMENT        PIC X(10).
       01 WS-AGEBAND        PIC X(6).
       01 WS-RISK           PIC 9.
       01 WS-COUNTS.
          05 WS-CNT-CREDIT  PIC 9(3) VALUE 0.
          05 WS-CNT-DEFAULT PIC 9(3) VALUE 0.
          05 WS-CNT-WATCH   PIC 9(3) VALUE 0.
          05 WS-CNT-NORMAL  PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CUST-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CUST-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM CLASSIFY-ONE
               END-READ
           END-PERFORM
           CLOSE CUST-FILE
           DISPLAY "CREDIT " WS-CNT-CREDIT " DEFAULT " WS-CNT-DEFAULT
                   " WATCH " WS-CNT-WATCH " NORMAL " WS-CNT-NORMAL
           STOP RUN.

       CLASSIFY-ONE.
           EVALUATE TRUE
               WHEN CU-BALANCE < 0
                   MOVE "CREDIT" TO WS-CLASS
                   ADD 1 TO WS-CNT-CREDIT
               WHEN CU-DAYS-LATE > 90
                   MOVE "DEFAULT" TO WS-CLASS
                   ADD 1 TO WS-CNT-DEFAULT
               WHEN CU-DAYS-LATE > 30 AND CU-BALANCE > 1000
                   MOVE "WATCH" TO WS-CLASS
                   ADD 1 TO WS-CNT-WATCH
               WHEN OTHER
                   MOVE "NORMAL" TO WS-CLASS
                   ADD 1 TO WS-CNT-NORMAL
           END-EVALUATE
           EVALUATE CU-TYPE ALSO TRUE
               WHEN "P" ALSO CU-AGE < 25
                   MOVE "YOUNG-P" TO WS-SEGMENT
               WHEN "P" ALSO CU-AGE >= 65
                   MOVE "SENIOR-P" TO WS-SEGMENT
               WHEN "P" ALSO ANY
                   MOVE "PERSONAL" TO WS-SEGMENT
               WHEN "B" ALSO ANY
                   MOVE "BUSINESS" TO WS-SEGMENT
               WHEN "G" THRU "J" ALSO ANY
                   MOVE "PUBLIC" TO WS-SEGMENT
               WHEN OTHER
                   MOVE "UNKNOWN" TO WS-SEGMENT
           END-EVALUATE
           IF CU-TYPE = "B"
               IF CU-BALANCE > 50000 OR CU-DAYS-LATE > 60
                   MOVE 3 TO WS-RISK
               ELSE
                   IF CU-BALANCE > 10000
                       MOVE 2 TO WS-RISK
                   ELSE
                       MOVE 1 TO WS-RISK
                   END-IF
               END-IF
           ELSE
               IF CU-DAYS-LATE = 0 AND NOT CU-BALANCE < 0
                   MOVE 0 TO WS-RISK
               ELSE
                   IF CU-DAYS-LATE > 30 OR CU-BALANCE < -500
                       MOVE 2 TO WS-RISK
                   ELSE
                       MOVE 1 TO WS-RISK
                   END-IF
               END-IF
           END-IF
           EVALUATE CU-AGE
               WHEN 0 THRU 17
                   MOVE "MINOR" TO WS-AGEBAND
               WHEN 18 THRU 64
                   MOVE "ADULT" TO WS-AGEBAND
               WHEN OTHER
                   MOVE "SENIOR" TO WS-AGEBAND
           END-EVALUATE
           DISPLAY CU-ID " " WS-CLASS " " WS-SEGMENT " " WS-RISK " "
                   WS-AGEBAND.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
