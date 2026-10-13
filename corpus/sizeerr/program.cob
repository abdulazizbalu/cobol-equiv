      * cobol-equiv corpus: SIZEERR (MIT licensed)
      * Running accumulators with and without ON SIZE ERROR.
      * Semantic area: size error leaves the target unchanged,
      * high-order truncation without the phrase, division by zero,
      * DIVIDE ... REMAINDER.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SIZEERR.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TXN-FILE ASSIGN TO "TXN.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD TXN-FILE.
       01 TXN-REC.
          05 TX-ACCT        PIC X(4).
          05 TX-OP          PIC X.
          05 TX-AMOUNT      PIC S9(5)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-ACC            PIC S9(5)V99 COMP-3 VALUE 0.
       01 WS-RAW            PIC S9(5)V99 VALUE 0.
       01 WS-BIN            PIC S9(4) COMP VALUE 0.
       01 WS-QUOT           PIC S9(3)V9 VALUE 0.
       01 WS-REM            PIC S9(5)V99 VALUE 0.
       01 WS-ERRORS         PIC 9(4) VALUE 0.
       01 WS-COUNT          PIC 9(4) VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT TXN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ TXN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM APPLY-TXN
               END-READ
           END-PERFORM
           CLOSE TXN-FILE
           DISPLAY "COUNT " WS-COUNT " ERRORS " WS-ERRORS
           DISPLAY "FINAL " WS-ACC " " WS-RAW " " WS-BIN
           STOP RUN.

       APPLY-TXN.
           ADD 1 TO WS-COUNT
           EVALUATE TX-OP
               WHEN "A"
                   ADD TX-AMOUNT TO WS-ACC
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-ADD
                   ADD TX-AMOUNT TO WS-RAW WS-BIN
               WHEN "S"
                   SUBTRACT TX-AMOUNT FROM WS-ACC
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-SUBTRACT
                   SUBTRACT TX-AMOUNT FROM WS-RAW WS-BIN
               WHEN "M"
                   MULTIPLY TX-AMOUNT BY WS-ACC ROUNDED
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-MULTIPLY
                   MULTIPLY TX-AMOUNT BY WS-RAW ROUNDED WS-BIN
               WHEN "D"
                   DIVIDE TX-AMOUNT INTO WS-ACC ROUNDED
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR PERFORM SHOW-OK
                   END-DIVIDE
                   DIVIDE TX-AMOUNT INTO WS-RAW ROUNDED
               WHEN "Q"
                   DIVIDE WS-ACC BY TX-AMOUNT
                       GIVING WS-QUOT REMAINDER WS-REM
                       ON SIZE ERROR PERFORM SHOW-ERROR
                       NOT ON SIZE ERROR
                           DISPLAY TX-ACCT " Q " WS-QUOT " R " WS-REM
                   END-DIVIDE
               WHEN OTHER
                   DISPLAY TX-ACCT " BAD OPERATION " TX-OP
           END-EVALUATE.

       SHOW-OK.
           DISPLAY TX-ACCT " OK    " TX-OP " " WS-ACC " " WS-RAW " "
               WS-BIN.

       SHOW-ERROR.
           ADD 1 TO WS-ERRORS
           DISPLAY TX-ACCT " ERROR " TX-OP " " WS-ACC " " WS-RAW " "
               WS-BIN.
