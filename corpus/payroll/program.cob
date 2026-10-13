      * cobol-equiv corpus: PAYROLL (MIT licensed)
      * Payroll with COMP-3 working storage and signed values.
      * Semantic area: packed decimal, signs, overpunch input and
      * output, ROUNDED, EVALUATE on codes.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYROLL.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMP-FILE ASSIGN TO "EMPLOYEES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT PAY-FILE ASSIGN TO "PAYOUT.DAT"
               ORGANIZATION IS SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD EMP-FILE.
       01 EMP-REC.
          05 EMP-ID         PIC X(5).
          05 EMP-NAME       PIC X(10).
          05 EMP-HOURS      PIC 9(3)V9.
          05 EMP-RATE       PIC 9(3)V99.
          05 EMP-DED-CODE   PIC X.
          05 EMP-ADJUST     PIC S9(5)V99.
       FD PAY-FILE.
       01 PAY-REC.
          05 PAY-ID         PIC X(5).
          05 PAY-GROSS      PIC S9(7)V99 COMP-3.
          05 PAY-NET        PIC S9(7)V99 COMP-3.
          05 PAY-NET-D      PIC S9(7)V99.
          05 PAY-FLAG       PIC X.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-OT-HOURS       PIC S9(3)V9 COMP-3.
       01 WS-GROSS          PIC S9(7)V99 COMP-3.
       01 WS-TAX            PIC S9(7)V99 COMP-3.
       01 WS-DED            PIC S9(5)V99 COMP-3.
       01 WS-NET            PIC S9(7)V99 COMP-3.
       01 WS-TOT-GROSS      PIC S9(9)V99 COMP-3 VALUE 0.
       01 WS-TOT-NET        PIC S9(9)V99 COMP-3 VALUE 0.
       01 WS-NEG-COUNT      PIC 9(3) COMP-3 VALUE 0.
       01 WS-EMP-COUNT      PIC 9(3) COMP-3 VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT EMP-FILE OUTPUT PAY-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ EMP-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PAY-ONE
               END-READ
           END-PERFORM
           CLOSE EMP-FILE PAY-FILE
           DISPLAY "EMPLOYEES " WS-EMP-COUNT
           DISPLAY "TOTAL GROSS " WS-TOT-GROSS
           DISPLAY "TOTAL NET   " WS-TOT-NET
           DISPLAY "NEGATIVE NET " WS-NEG-COUNT
           STOP RUN.

       PAY-ONE.
           ADD 1 TO WS-EMP-COUNT
           IF EMP-HOURS > 40
               COMPUTE WS-OT-HOURS = EMP-HOURS - 40
               COMPUTE WS-GROSS ROUNDED =
                   40 * EMP-RATE + WS-OT-HOURS * EMP-RATE * 1.5
           ELSE
               MOVE 0 TO WS-OT-HOURS
               COMPUTE WS-GROSS ROUNDED = EMP-HOURS * EMP-RATE
           END-IF
           EVALUATE TRUE
               WHEN WS-GROSS <= 1000
                   COMPUTE WS-TAX ROUNDED = WS-GROSS * 0.10
               WHEN WS-GROSS <= 5000
                   COMPUTE WS-TAX ROUNDED =
                       100 + (WS-GROSS - 1000) * 0.25
               WHEN OTHER
                   COMPUTE WS-TAX ROUNDED =
                       1100 + (WS-GROSS - 5000) * 0.35
           END-EVALUATE
           EVALUATE EMP-DED-CODE
               WHEN "A"
                   MOVE 50 TO WS-DED
               WHEN "B"
                   COMPUTE WS-DED ROUNDED = WS-GROSS * 0.045
               WHEN "C"
                   MOVE 0 TO WS-DED
               WHEN OTHER
                   MOVE 25.50 TO WS-DED
           END-EVALUATE
           COMPUTE WS-NET = WS-GROSS - WS-TAX - WS-DED + EMP-ADJUST
           MOVE SPACE TO PAY-FLAG
           IF WS-NET < 0
               ADD 1 TO WS-NEG-COUNT
               MOVE "N" TO PAY-FLAG
           END-IF
           ADD WS-GROSS TO WS-TOT-GROSS
           ADD WS-NET TO WS-TOT-NET
           MOVE EMP-ID TO PAY-ID
           MOVE WS-GROSS TO PAY-GROSS
           MOVE WS-NET TO PAY-NET
           MOVE WS-NET TO PAY-NET-D
           WRITE PAY-REC
           DISPLAY EMP-ID " " EMP-NAME " " WS-GROSS " " WS-TAX " "
               WS-DED " " WS-NET.
