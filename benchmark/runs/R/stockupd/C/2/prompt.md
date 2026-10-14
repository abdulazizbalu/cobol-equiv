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
input_files = {'TRANS.DAT': b'1010R000\n'}
expected stdout = b'1010 BOLT    0500 O\n1020 NUT     0300 O\n1110 WASHER  0050 O\n2005 GEAR    0010 L\n2500 SHAFT   0000 E\n3300 SPRING  0120 O\n4001 PULLEY  0007 L\n7777 BELT    0999 O\nR 001 I 000 A 000 E 000\nIN 000000 OUT 000000 SHORT 000000 LAST [1010]\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'TRANS.DAT': b'1020-005\n'}
expected stdout = b'1010 BOLT    0500 O\n1020 NUT     0295 O\n1110 WASHER  0050 O\n2005 GEAR    0010 L\n2500 SHAFT   0000 E\n3300 SPRING  0120 O\n4001 PULLEY  0007 L\n7777 BELT    0999 O\nR 000 I 000 A 001 E 000\nIN 000000 OUT 000000 SHORT 000000 LAST [1020]\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. STOCKUPD.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRAN-FILE ASSIGN TO "TRANS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD TRAN-FILE.
       01 TRAN-REC.
          05 TR-PART        PIC 9(4).
          05 TR-CODE        PIC X.
             88 TR-RECEIPT  VALUE "R".
             88 TR-ISSUE    VALUE "I".
             88 TR-ADJUST   VALUE "+" "-".
             88 TR-PLUS     VALUE "+".
          05 TR-QTY         PIC 9(3).
             88 TR-BULK     VALUE 500 THRU 999.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
          88 END-OF-FILE    VALUE "Y".
       01 PART-DATA.
          05 FILLER PIC X(15) VALUE "1010BOLT   0500".
          05 FILLER PIC X(15) VALUE "1020NUT    0300".
          05 FILLER PIC X(15) VALUE "1110WASHER 0050".
          05 FILLER PIC X(15) VALUE "2005GEAR   0010".
          05 FILLER PIC X(15) VALUE "2500SHAFT  0000".
          05 FILLER PIC X(15) VALUE "3300SPRING 0120".
          05 FILLER PIC X(15) VALUE "4001PULLEY 0007".
          05 FILLER PIC X(15) VALUE "7777BELT   0999".
       01 PART-TABLE REDEFINES PART-DATA.
          05 PT-ENTRY OCCURS 8 TIMES
                ASCENDING KEY IS PT-PART INDEXED BY PX.
             10 PT-PART     PIC 9(4).
             10 PT-NAME     PIC X(7).
             10 PT-ONHAND   PIC 9(4).
       01 WS-SUMMARY.
          05 SM-COUNTS.
             10 SM-RECEIPTS PIC 9(3).
             10 SM-ISSUES   PIC 9(3).
             10 SM-ADJUSTS  PIC 9(3).
             10 SM-ERRORS   PIC 9(3).
          05 SM-QTY.
             10 SM-IN       PIC 9(6).
             10 SM-OUT      PIC 9(6).
             10 SM-SHORT    PIC 9(6).
          05 SM-LAST-PART   PIC X(4).
       01 WS-STATUS         PIC X.
          88 ST-OK          VALUE "O".
          88 ST-LOW         VALUE "L".
          88 ST-EMPTY       VALUE "E".
       01 WS-SHORT          PIC 9(3).
       PROCEDURE DIVISION.
       MAIN-LOGIC SECTION.
       MAIN-START.
           MOVE ALL "X" TO WS-SUMMARY
           INITIALIZE WS-SUMMARY
           OPEN INPUT TRAN-FILE
           PERFORM UNTIL END-OF-FILE
               READ TRAN-FILE
                   AT END SET END-OF-FILE TO TRUE
                   NOT AT END PERFORM APPLY-TRAN
               END-READ
           END-PERFORM
           CLOSE TRAN-FILE
           PERFORM PRINT-STOCK
           STOP RUN.

       APPLY-TRAN SECTION.
       APPLY-START.
           SEARCH ALL PT-ENTRY
               AT END
                   ADD 1 TO SM-ERRORS
                   DISPLAY "UNKNOWN PART " TR-PART
                   EXIT SECTION
               WHEN PT-PART (PX) = TR-PART
                   MOVE TR-PART TO SM-LAST-PART
           END-SEARCH
           EVALUATE TRUE
               WHEN TR-RECEIPT
                   ADD 1 TO SM-RECEIPTS
                   ADD TR-QTY TO PT-ONHAND (PX) SM-IN
                   IF TR-BULK
                       DISPLAY "BULK RECEIPT " TR-PART " " TR-QTY
                   END-IF
               WHEN TR-ISSUE
                   ADD 1 TO SM-ISSUES
                   PERFORM ISSUE-STOCK
               WHEN TR-ADJUST
                   ADD 1 TO SM-ADJUSTS
                   IF TR-PLUS
                       ADD TR-QTY TO PT-ONHAND (PX)
                   ELSE
                       IF TR-QTY > PT-ONHAND (PX)
                           MOVE 0 TO PT-ONHAND (PX)
                       ELSE
                           SUBTRACT TR-QTY FROM PT-ONHAND (PX)
                       END-IF
                   END-IF
               WHEN OTHER
                   ADD 1 TO SM-ERRORS
                   DISPLAY "BAD CODE " TR-PART " [" TR-CODE "]"
           END-EVALUATE.
       APPLY-END.
           EXIT.

       ISSUE-STOCK SECTION.
       ISSUE-START.
           IF TR-QTY > PT-ONHAND (PX)
               COMPUTE WS-SHORT = TR-QTY - PT-ONHAND (PX)
               ADD WS-SHORT TO SM-SHORT
               ADD PT-ONHAND (PX) TO SM-OUT
               MOVE 0 TO PT-ONHAND (PX)
               DISPLAY "SHORT " TR-PART " " WS-SHORT
           ELSE
               SUBTRACT TR-QTY FROM PT-ONHAND (PX)
               ADD TR-QTY TO SM-OUT
           END-IF.

       PRINT-STOCK SECTION.
       PRINT-START.
           PERFORM VARYING PX FROM 1 BY 1 UNTIL PX > 8
               EVALUATE TRUE
                   WHEN PT-ONHAND (PX) = 0
                       SET ST-EMPTY TO TRUE
                   WHEN PT-ONHAND (PX) < 20
                       SET ST-LOW TO TRUE
                   WHEN OTHER
                       SET ST-OK TO TRUE
               END-EVALUATE
               DISPLAY PT-PART (PX) " " PT-NAME (PX) " "
                   PT-ONHAND (PX) " " WS-STATUS
           END-PERFORM
           DISPLAY "R " SM-RECEIPTS " I " SM-ISSUES " A " SM-ADJUSTS
               " E " SM-ERRORS
           DISPLAY "IN " SM-IN " OUT " SM-OUT " SHORT " SM-SHORT
               " LAST [" SM-LAST-PART "]".
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
