      * Finding: ADD ... ROUNDED into COMP-3 (GnuCOBOL ticket #934).
       IDENTIFICATION DIVISION.
       PROGRAM-ID. RNDC3.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 A          PIC S9V999 VALUE 0.005.
       01 T          PIC S9(5)V99 COMP-3 VALUE 1.
       01 D          PIC S9(5)V99 VALUE 1.
       PROCEDURE DIVISION.
           ADD A TO T ROUNDED
           ADD A TO D ROUNDED
           DISPLAY "COMP-3 " T " DISPLAY " D
           STOP RUN.
