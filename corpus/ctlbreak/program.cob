      * cobol-equiv corpus: CTLBREAK (MIT licensed)
      * Sales report with a two-level control break. Semantic area:
      * sequential file processing, control breaks, totals written
      * to a LINE SEQUENTIAL report with edited signed amounts.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CTLBREAK.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SALES-FILE ASSIGN TO "SALES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT REPORT-FILE ASSIGN TO "REPORT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD SALES-FILE.
       01 SALES-REC.
          05 SL-REGION      PIC X(2).
          05 SL-BRANCH      PIC X(3).
          05 SL-AMOUNT      PIC S9(5)V99.
       FD REPORT-FILE.
       01 REPORT-LINE       PIC X(40).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-FIRST          PIC X VALUE "Y".
       01 WS-PREV-REGION    PIC X(2).
       01 WS-PREV-BRANCH    PIC X(3).
       01 WS-BRANCH-TOT     PIC S9(7)V99.
       01 WS-BRANCH-CNT     PIC 9(4).
       01 WS-REGION-TOT     PIC S9(8)V99.
       01 WS-GRAND-TOT      PIC S9(9)V99 VALUE 0.
       01 WS-GRAND-CNT      PIC 9(5) VALUE 0.
       01 BRANCH-LINE.
          05 FILLER         PIC X(4) VALUE SPACES.
          05 BL-REGION      PIC X(2).
          05 FILLER         PIC X VALUE "/".
          05 BL-BRANCH      PIC X(3).
          05 FILLER         PIC X VALUE SPACE.
          05 BL-COUNT       PIC ZZZ9.
          05 FILLER         PIC X VALUE SPACE.
          05 BL-TOTAL       PIC Z,ZZZ,ZZ9.99CR.
       01 REGION-LINE.
          05 FILLER         PIC X(7) VALUE "REGION ".
          05 RL-REGION      PIC X(2).
          05 FILLER         PIC X(6) VALUE " TOTAL".
          05 RL-TOTAL       PIC ---,---,--9.99.
       01 GRAND-LINE.
          05 FILLER         PIC X(6) VALUE "GRAND ".
          05 GL-COUNT       PIC ZZ,ZZ9.
          05 FILLER         PIC X VALUE SPACE.
          05 GL-TOTAL       PIC $$$$,$$$,$$9.99-.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT SALES-FILE OUTPUT REPORT-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ SALES-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PROCESS-SALE
               END-READ
           END-PERFORM
           IF WS-FIRST = "Y"
               MOVE "NO DATA" TO REPORT-LINE
               WRITE REPORT-LINE
           ELSE
               PERFORM BRANCH-BREAK
               PERFORM REGION-BREAK
           END-IF
           MOVE WS-GRAND-CNT TO GL-COUNT
           MOVE WS-GRAND-TOT TO GL-TOTAL
           WRITE REPORT-LINE FROM GRAND-LINE
           CLOSE SALES-FILE REPORT-FILE
           STOP RUN.

       PROCESS-SALE.
           IF WS-FIRST = "Y"
               MOVE "N" TO WS-FIRST
               MOVE SL-REGION TO WS-PREV-REGION
               MOVE SL-BRANCH TO WS-PREV-BRANCH
               MOVE 0 TO WS-BRANCH-TOT WS-BRANCH-CNT WS-REGION-TOT
           ELSE
               IF SL-REGION NOT = WS-PREV-REGION
                   PERFORM BRANCH-BREAK
                   PERFORM REGION-BREAK
               ELSE
                   IF SL-BRANCH NOT = WS-PREV-BRANCH
                       PERFORM BRANCH-BREAK
                   END-IF
               END-IF
           END-IF
           ADD SL-AMOUNT TO WS-BRANCH-TOT
           ADD 1 TO WS-BRANCH-CNT WS-GRAND-CNT.

       BRANCH-BREAK.
           MOVE WS-PREV-REGION TO BL-REGION
           MOVE WS-PREV-BRANCH TO BL-BRANCH
           MOVE WS-BRANCH-CNT TO BL-COUNT
           MOVE WS-BRANCH-TOT TO BL-TOTAL
           WRITE REPORT-LINE FROM BRANCH-LINE
           ADD WS-BRANCH-TOT TO WS-REGION-TOT
           MOVE 0 TO WS-BRANCH-TOT WS-BRANCH-CNT
           MOVE SL-BRANCH TO WS-PREV-BRANCH.

       REGION-BREAK.
           MOVE WS-PREV-REGION TO RL-REGION
           MOVE WS-REGION-TOT TO RL-TOTAL
           WRITE REPORT-LINE FROM REGION-LINE
           ADD WS-REGION-TOT TO WS-GRAND-TOT
           MOVE 0 TO WS-REGION-TOT
           MOVE SL-REGION TO WS-PREV-REGION.
