      * cobol-equiv corpus: REGSUM (MIT licensed)
      * Monthly sales per region; the input is sorted by region.
      * Semantic area: INITIALIZE of a multi-level group with OCCURS
      * and alphanumeric, numeric and numeric-edited items, control break.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. REGSUM.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SALES-FILE ASSIGN TO "SALES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD SALES-FILE.
       01 SALES-REC.
          05 SL-REGION      PIC X(2).
          05 SL-MONTH       PIC 99.
          05 SL-AMOUNT      PIC S9(5)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-FIRST          PIC X VALUE "Y".
       01 WS-REGION-SUM.
          05 RS-REGION      PIC X(2).
          05 RS-NAME        PIC X(10).
          05 RS-MONTHS.
             10 RS-MONTH OCCURS 12 TIMES.
                15 RS-AMT   PIC S9(6)V99.
                15 RS-CNT   PIC 9(3).
          05 RS-TOTALS.
             10 RS-TOTAL    PIC S9(7)V99.
             10 RS-BEST     PIC 99.
             10 RS-SHOWN    PIC -(6)9.99.
       01 WS-M              PIC 99.
       01 WS-REJECTS        PIC 9(3) VALUE 0.
       01 WS-OUT-AMT        PIC -(6)9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           INITIALIZE WS-REGION-SUM
           OPEN INPUT SALES-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ SALES-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM ADD-SALE
               END-READ
           END-PERFORM
           CLOSE SALES-FILE
           IF WS-FIRST = "N"
               PERFORM PRINT-REGION
           END-IF
           DISPLAY "REJECTED " WS-REJECTS
           STOP RUN.

       ADD-SALE.
           IF SL-MONTH < 1 OR SL-MONTH > 12
               ADD 1 TO WS-REJECTS
           ELSE
               IF WS-FIRST = "N" AND SL-REGION NOT = RS-REGION
                   PERFORM PRINT-REGION
                   INITIALIZE WS-REGION-SUM
               END-IF
               MOVE "N" TO WS-FIRST
               MOVE SL-REGION TO RS-REGION
               STRING "REGION " SL-REGION DELIMITED BY SIZE
                   INTO RS-NAME
               ADD SL-AMOUNT TO RS-AMT (SL-MONTH) RS-TOTAL
               ADD 1 TO RS-CNT (SL-MONTH)
           END-IF.

       PRINT-REGION.
           MOVE 1 TO RS-BEST
           PERFORM VARYING WS-M FROM 1 BY 1 UNTIL WS-M > 12
               IF RS-CNT (WS-M) > 0
                   MOVE RS-AMT (WS-M) TO WS-OUT-AMT
                   DISPLAY RS-REGION " " WS-M " " WS-OUT-AMT " "
                       RS-CNT (WS-M)
               END-IF
               IF RS-AMT (WS-M) > RS-AMT (RS-BEST)
                   MOVE WS-M TO RS-BEST
               END-IF
           END-PERFORM
           MOVE RS-TOTAL TO RS-SHOWN
           DISPLAY RS-NAME " TOTAL " RS-SHOWN " BEST " RS-BEST.
