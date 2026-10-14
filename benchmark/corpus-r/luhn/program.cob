      * cobol-equiv corpus: LUHN (MIT licensed)
      * Luhn check digits of card numbers, digits left-justified in
      * X(16). Semantic area: reference modification in a loop, class
      * test NUMERIC, INSPECT TALLYING, DIVIDE ... REMAINDER, MOVE of a
      * one-digit alphanumeric item to a numeric item.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. LUHN.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CARD-FILE ASSIGN TO "CARDS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CARD-FILE.
       01 CARD-REC.
          05 CD-NUMBER      PIC X(16).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-LEN            PIC 99.
       01 WS-POS            PIC 99.
       01 WS-DIGIT          PIC 9.
       01 WS-DOUBLE         PIC 99.
       01 WS-SUM            PIC 9(3).
       01 WS-QUOT           PIC 9(3).
       01 WS-REM            PIC 9.
       01 WS-CHECK          PIC 9.
       01 WS-ODD            PIC X.
       01 WS-VALID          PIC 9(3) VALUE 0.
       01 WS-INVALID        PIC 9(3) VALUE 0.
       01 WS-REJECTED       PIC 9(3) VALUE 0.
       01 WS-FIXED          PIC X(16).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CARD-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CARD-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM CHECK-CARD
               END-READ
           END-PERFORM
           CLOSE CARD-FILE
           DISPLAY "VALID " WS-VALID " INVALID " WS-INVALID
               " REJECTED " WS-REJECTED
           STOP RUN.

       CHECK-CARD.
           MOVE 0 TO WS-LEN
           INSPECT CD-NUMBER TALLYING WS-LEN
               FOR CHARACTERS BEFORE INITIAL SPACE
           IF WS-LEN < 2
               ADD 1 TO WS-REJECTED
               DISPLAY "SHORT [" CD-NUMBER "]"
           ELSE
               IF CD-NUMBER (1:WS-LEN) IS NOT NUMERIC
                   ADD 1 TO WS-REJECTED
                   DISPLAY "NOT NUMERIC [" CD-NUMBER (1:WS-LEN) "]"
               ELSE
                   PERFORM LUHN-SUM
                   PERFORM REPORT-CARD
               END-IF
           END-IF.

       LUHN-SUM.
           MOVE 0 TO WS-SUM
           MOVE "N" TO WS-ODD
           PERFORM VARYING WS-POS FROM WS-LEN BY -1 UNTIL WS-POS < 2
               MOVE CD-NUMBER (WS-POS - 1:1) TO WS-DIGIT
               IF WS-ODD = "N"
                   MULTIPLY WS-DIGIT BY 2 GIVING WS-DOUBLE
                   IF WS-DOUBLE > 9
                       SUBTRACT 9 FROM WS-DOUBLE
                   END-IF
                   ADD WS-DOUBLE TO WS-SUM
                   MOVE "Y" TO WS-ODD
               ELSE
                   ADD WS-DIGIT TO WS-SUM
                   MOVE "N" TO WS-ODD
               END-IF
           END-PERFORM
           DIVIDE WS-SUM BY 10 GIVING WS-QUOT REMAINDER WS-REM
           IF WS-REM = 0
               MOVE 0 TO WS-CHECK
           ELSE
               COMPUTE WS-CHECK = 10 - WS-REM
           END-IF.

       REPORT-CARD.
           MOVE CD-NUMBER (WS-LEN:1) TO WS-DIGIT
           IF WS-DIGIT = WS-CHECK
               ADD 1 TO WS-VALID
               DISPLAY "VALID " CD-NUMBER (1:WS-LEN)
           ELSE
               ADD 1 TO WS-INVALID
               MOVE CD-NUMBER TO WS-FIXED
               MOVE WS-CHECK TO WS-FIXED (WS-LEN:1)
               DISPLAY "INVALID " CD-NUMBER (1:WS-LEN) " SUM " WS-SUM
                   " EXPECTED " WS-FIXED
           END-IF.
