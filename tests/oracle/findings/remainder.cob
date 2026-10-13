      * Finding: REMAINDER stored despite quotient size error.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. REMSE.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 A          PIC S9(5) VALUE 12345.
       01 B          PIC S9(3) VALUE 10.
       01 Q          PIC S9(2) VALUE 7.
       01 R          PIC S9(3) VALUE 9.
       PROCEDURE DIVISION.
           DIVIDE A BY B GIVING Q REMAINDER R
               ON SIZE ERROR DISPLAY "SIZE ERROR"
           END-DIVIDE
           DISPLAY "Q " Q " R " R
           STOP RUN.
