      * cobol-equiv runner test program: TALLY (MIT licensed)
      * Used only to test the translation runner; not part of the
      * benchmark corpus.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TALLY.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-FILE ASSIGN TO "VALUES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD IN-FILE.
       01 IN-REC.
          05 IN-CODE        PIC X.
          05 IN-AMT         PIC 9(3)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-COUNT          PIC 9(3) VALUE 0.
       01 WS-TOTAL          PIC 9(5)V99 VALUE 0.
       01 WS-OUT            PIC ZZ,ZZ9.99.
       PROCEDURE DIVISION.
           OPEN INPUT IN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ IN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END
                       IF IN-CODE = "A"
                           ADD 1 TO WS-COUNT
                           ADD IN-AMT TO WS-TOTAL
                       END-IF
               END-READ
           END-PERFORM
           CLOSE IN-FILE
           MOVE WS-TOTAL TO WS-OUT
           DISPLAY "COUNT " WS-COUNT " TOTAL " WS-OUT
           STOP RUN.
