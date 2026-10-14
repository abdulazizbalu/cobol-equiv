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
input_files = {'RECS.DAT': b'H                    00000000\n'}
expected stdout = b'HEADER                      0000-00-00 N 00000000\nOPEN COUNT 00000 TOTAL +000000000.00\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'RECS.DAT': b'HCD0LPR0TW2L1UP4Y8X6200000000\n'}
expected stdout = b'HEADER CD0LPR0TW2L1UP4Y8X62 0000-00-00 N 00000000\nOPEN COUNT 00000 TOTAL +000000000.00\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. REDEF.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT REC-FILE ASSIGN TO "RECS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD REC-FILE.
       01 IN-REC.
          05 IR-TYPE        PIC X.
          05 IR-BODY        PIC X(29).
          05 IR-HEADER REDEFINES IR-BODY.
             10 IH-NAME     PIC X(20).
             10 IH-DATE     PIC 9(8).
             10 IH-DATE-R REDEFINES IH-DATE.
                15 IH-YYYY  PIC 9(4).
                15 IH-MM    PIC 99.
                15 IH-DD    PIC 99.
             10 FILLER      PIC X.
          05 IR-DETAIL REDEFINES IR-BODY.
             10 ID-ITEM     PIC X(5).
             10 ID-QTY      PIC S9(4).
             10 ID-PRICE    PIC 9(5)V99.
             10 ID-DISC     PIC V99.
             10 FILLER      PIC X(11).
          05 IR-TRAILER REDEFINES IR-BODY.
             10 IT-COUNT    PIC 9(5).
             10 IT-TOTAL    PIC S9(9)V99.
             10 FILLER      PIC X(13).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-DAYS-TEXT      PIC X(24)
                            VALUE "312931303130313130313031".
       01 WS-DAYS-TABLE REDEFINES WS-DAYS-TEXT.
          05 WS-DAYS        PIC 99 OCCURS 12.
       01 WS-RUN-COUNT      PIC 9(5) VALUE 0.
       01 WS-RUN-TOTAL      PIC S9(9)V99 VALUE 0.
       01 WS-LINE-AMT       PIC S9(9)V99.
       01 WS-LINE-ED        PIC ---,---,--9.99.
       01 WS-DATE-OK        PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT REC-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ REC-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM DO-RECORD
               END-READ
           END-PERFORM
           CLOSE REC-FILE
           DISPLAY "OPEN COUNT " WS-RUN-COUNT " TOTAL " WS-RUN-TOTAL
           STOP RUN.

       DO-RECORD.
           EVALUATE IR-TYPE
               WHEN "H"
                   PERFORM DO-HEADER
               WHEN "D"
                   PERFORM DO-DETAIL
               WHEN "T"
                   PERFORM DO-TRAILER
               WHEN OTHER
                   DISPLAY "UNKNOWN TYPE " IR-TYPE
           END-EVALUATE.

       DO-HEADER.
           MOVE "Y" TO WS-DATE-OK
           IF IH-MM < 1 OR IH-MM > 12
               MOVE "N" TO WS-DATE-OK
           ELSE
               IF IH-DD < 1 OR IH-DD > WS-DAYS (IH-MM)
                   MOVE "N" TO WS-DATE-OK
               END-IF
           END-IF
           DISPLAY "HEADER " IH-NAME " " IH-YYYY "-" IH-MM "-" IH-DD
                   " " WS-DATE-OK " " IH-DATE.

       DO-DETAIL.
           COMPUTE WS-LINE-AMT ROUNDED =
               ID-QTY * ID-PRICE * (1 - ID-DISC)
           MOVE WS-LINE-AMT TO WS-LINE-ED
           ADD 1 TO WS-RUN-COUNT
           ADD WS-LINE-AMT TO WS-RUN-TOTAL
           DISPLAY "DETAIL " ID-ITEM " " WS-LINE-ED.

       DO-TRAILER.
           IF IT-COUNT = WS-RUN-COUNT AND IT-TOTAL = WS-RUN-TOTAL
               DISPLAY "TRAILER OK " IT-COUNT
           ELSE
               DISPLAY "TRAILER MISMATCH " IT-COUNT " " IT-TOTAL
                       " " WS-RUN-COUNT " " WS-RUN-TOTAL
           END-IF
           MOVE 0 TO WS-RUN-COUNT WS-RUN-TOTAL.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
