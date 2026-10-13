      * Finding: COMP-5 not truncated to PICTURE; SIZE ERROR range.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. COMP5.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 S          PIC S9(6) VALUE 99999.
       01 N          PIC S9(6) VALUE -32768.
       01 B5         PIC S9(4) COMP-5.
       01 BC         PIC S9(4) COMP.
       PROCEDURE DIVISION.
           MOVE S TO B5 BC
           DISPLAY "MOVE 99999 COMP-5 " B5 " COMP " BC
           MOVE 0 TO B5
           ADD N TO B5 ON SIZE ERROR DISPLAY "ADD -32768 SIZE ERROR"
               NOT ON SIZE ERROR DISPLAY "ADD -32768 OK"
           END-ADD
           DISPLAY "B5 " B5
           MOVE 0 TO B5
           MOVE 12345 TO S
           ADD S TO B5 ON SIZE ERROR DISPLAY "ADD 12345 SIZE ERROR"
               NOT ON SIZE ERROR DISPLAY "ADD 12345 OK"
           END-ADD
           DISPLAY "B5 " B5
           STOP RUN.
