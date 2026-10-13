      * Finding: INSPECT with several phrases.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INSP.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 X          PIC X(6) VALUE "ABCABC".
       01 Y          PIC X(6).
       01 Z          PIC X(4) VALUE "0000".
       01 C1         PIC 99 VALUE 0.
       01 C2         PIC 99 VALUE 0.
       PROCEDURE DIVISION.
           INSPECT X TALLYING C1 FOR ALL "BC" C2 FOR ALL "AB"
           DISPLAY "TALLY BC/AB " C1 " " C2
           MOVE X TO Y
           INSPECT Y REPLACING ALL "BC" BY "xy" ALL "AB" BY "pq"
           DISPLAY "REPLACE " Y
           MOVE 0 TO C1 C2
           INSPECT Z TALLYING C1 FOR LEADING "0" C2 FOR CHARACTERS
           DISPLAY "LEADING/CHARACTERS " C1 " " C2
           STOP RUN.
