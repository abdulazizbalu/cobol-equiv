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
input_files = {'DATES.DAT': b'2000010120000101000000\n'}
expected stdout = b'20000101 20000101        0 SAT 20000101\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'DATES.DAT': b'2026130102097152631447\n'}
expected stdout = b'20261301 INVALID FROM DATE\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. DATECALC.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT DATE-FILE ASSIGN TO "DATES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD DATE-FILE.
       01 DATE-REC.
          05 DT-FROM        PIC 9(8).
          05 DT-TO          PIC 9(8).
          05 DT-OFFSET      PIC S9(6).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-CUM-TEXT       PIC X(36)
                  VALUE "000031059090120151181212243273304334".
       01 WS-CUM-TABLE REDEFINES WS-CUM-TEXT.
          05 WS-CUM         PIC 999 OCCURS 12.
       01 WS-DIM-TEXT       PIC X(24)
                  VALUE "312831303130313130313031".
       01 WS-DIM-TABLE REDEFINES WS-DIM-TEXT.
          05 WS-DIM         PIC 99 OCCURS 12.
       01 WS-DOW-TEXT       PIC X(21)
                  VALUE "MONTUEWEDTHUFRISATSUN".
       01 WS-DOW-TABLE REDEFINES WS-DOW-TEXT.
          05 WS-DOW-NAME    PIC X(3) OCCURS 7.
       01 WS-DATE           PIC 9(8).
       01 WS-DATE-R REDEFINES WS-DATE.
          05 WS-YYYY        PIC 9(4).
          05 WS-MM          PIC 99.
          05 WS-DD          PIC 99.
       01 WS-VALID          PIC X.
       01 WS-LEAP           PIC X.
       01 WS-Q              PIC 9(7).
       01 WS-R4             PIC 9(4).
       01 WS-R100           PIC 9(4).
       01 WS-R400           PIC 9(4).
       01 WS-Y              PIC 9(5).
       01 WS-DAYNUM         PIC S9(8).
       01 WS-FROM-NUM       PIC S9(8).
       01 WS-TO-NUM         PIC S9(8).
       01 WS-NEW-NUM        PIC S9(8).
       01 WS-DIFF           PIC S9(8).
       01 WS-DIFF-ED        PIC -(7)9.
       01 WS-DOW-IX         PIC 9.
       01 WS-REM7           PIC 9.
       01 WS-MAXDAY         PIC 99.
       01 WS-RESULT         PIC X(8).
       01 WS-TRY            PIC S9(8).
       01 WS-DONE           PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT DATE-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ DATE-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM DO-PAIR
               END-READ
           END-PERFORM
           CLOSE DATE-FILE
           STOP RUN.

       DO-PAIR.
           MOVE DT-FROM TO WS-DATE
           PERFORM VALIDATE-DATE
           IF WS-VALID = "N"
               DISPLAY DT-FROM " INVALID FROM DATE"
               EXIT PARAGRAPH
           END-IF
           PERFORM DATE-TO-NUM
           MOVE WS-DAYNUM TO WS-FROM-NUM
           MOVE DT-TO TO WS-DATE
           PERFORM VALIDATE-DATE
           IF WS-VALID = "N"
               DISPLAY DT-TO " INVALID TO DATE"
               EXIT PARAGRAPH
           END-IF
           PERFORM DATE-TO-NUM
           MOVE WS-DAYNUM TO WS-TO-NUM
           COMPUTE WS-DIFF = WS-TO-NUM - WS-FROM-NUM
           MOVE WS-DIFF TO WS-DIFF-ED
           DIVIDE WS-FROM-NUM BY 7 GIVING WS-Q REMAINDER WS-REM7
           COMPUTE WS-DOW-IX = WS-REM7 + 1
           COMPUTE WS-NEW-NUM = WS-FROM-NUM + DT-OFFSET
           IF WS-NEW-NUM < 0 OR WS-NEW-NUM > 3067670
               MOVE "RANGE" TO WS-RESULT
           ELSE
               MOVE WS-NEW-NUM TO WS-DAYNUM
               PERFORM NUM-TO-DATE
               MOVE WS-DATE TO WS-RESULT
           END-IF
           DISPLAY DT-FROM " " DT-TO " " WS-DIFF-ED " "
                   WS-DOW-NAME (WS-DOW-IX) " " WS-RESULT.

       VALIDATE-DATE.
           MOVE "Y" TO WS-VALID
           IF WS-YYYY < 1601 OR WS-MM < 1 OR WS-MM > 12 OR WS-DD < 1
               MOVE "N" TO WS-VALID
           ELSE
               PERFORM CHECK-LEAP
               MOVE WS-DIM (WS-MM) TO WS-MAXDAY
               IF WS-MM = 2 AND WS-LEAP = "Y"
                   ADD 1 TO WS-MAXDAY
               END-IF
               IF WS-DD > WS-MAXDAY
                   MOVE "N" TO WS-VALID
               END-IF
           END-IF.

       CHECK-LEAP.
           DIVIDE WS-YYYY BY 4 GIVING WS-Q REMAINDER WS-R4
           DIVIDE WS-YYYY BY 100 GIVING WS-Q REMAINDER WS-R100
           DIVIDE WS-YYYY BY 400 GIVING WS-Q REMAINDER WS-R400
           IF WS-R4 = 0 AND (WS-R100 NOT = 0 OR WS-R400 = 0)
               MOVE "Y" TO WS-LEAP
           ELSE
               MOVE "N" TO WS-LEAP
           END-IF.

       DATE-TO-NUM.
           COMPUTE WS-Y = WS-YYYY - 1601
           DIVIDE WS-Y BY 4 GIVING WS-Q
           COMPUTE WS-DAYNUM = WS-Y * 365 + WS-Q
           DIVIDE WS-Y BY 100 GIVING WS-Q
           SUBTRACT WS-Q FROM WS-DAYNUM
           DIVIDE WS-Y BY 400 GIVING WS-Q
           ADD WS-Q TO WS-DAYNUM
           ADD WS-CUM (WS-MM) WS-DD TO WS-DAYNUM
           SUBTRACT 1 FROM WS-DAYNUM
           PERFORM CHECK-LEAP
           IF WS-LEAP = "Y" AND WS-MM > 2
               ADD 1 TO WS-DAYNUM
           END-IF.

       NUM-TO-DATE.
           MOVE WS-DAYNUM TO WS-TRY
           DIVIDE WS-DAYNUM BY 366 GIVING WS-Y
           COMPUTE WS-YYYY = WS-Y + 1601
           MOVE 1 TO WS-MM WS-DD
           MOVE "N" TO WS-DONE
           PERFORM UNTIL WS-DONE = "Y"
               IF WS-YYYY = 9999
                   MOVE "Y" TO WS-DONE
               ELSE
                   ADD 1 TO WS-YYYY
                   PERFORM DATE-TO-NUM
                   IF WS-DAYNUM > WS-TRY
                       SUBTRACT 1 FROM WS-YYYY
                       MOVE "Y" TO WS-DONE
                   END-IF
               END-IF
           END-PERFORM
           MOVE 12 TO WS-MM
           PERFORM DATE-TO-NUM
           PERFORM UNTIL WS-DAYNUM <= WS-TRY
               SUBTRACT 1 FROM WS-MM
               PERFORM DATE-TO-NUM
           END-PERFORM
           COMPUTE WS-DD = WS-TRY - WS-DAYNUM + 1.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
