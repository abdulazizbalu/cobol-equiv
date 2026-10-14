      * cobol-equiv corpus: STOCKUPD (MIT licensed)
      * Stock movements against a part table. Semantic area: SECTIONs,
      * level-88 conditions with several values and THRU, SET ... TO
      * TRUE, SEARCH ALL on a numeric key, INITIALIZE of a summary
      * group, EXIT SECTION.
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
