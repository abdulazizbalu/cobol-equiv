      * cobol-equiv corpus: LOANCALC (MIT licensed)
      * Fixed-point loan amortisation. Semantic area: COMPUTE with
      * ROUNDED, intermediate precision of division, ON SIZE ERROR.
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
