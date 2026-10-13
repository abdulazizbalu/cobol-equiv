      * Finding: fixed minus with floating currency (-$$$9.99).
       IDENTIFICATION DIVISION.
       PROGRAM-ID. EDMIN.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 S          PIC S9(5)V99.
       01 E          PIC -$$$9.99.
       PROCEDURE DIVISION.
           MOVE 5 TO S MOVE S TO E DISPLAY "+5    [" E "]"
           MOVE -5 TO S MOVE S TO E DISPLAY "-5    [" E "]"
           MOVE 1000 TO S MOVE S TO E DISPLAY "+1000 [" E "]"
           STOP RUN.
