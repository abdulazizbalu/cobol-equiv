      * Finding: value of 2**63 or more moved to a binary item.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HUGEC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 S          PIC S9(31)
                     VALUE -1000000000000000000000000000000.
       01 T          PIC S9(18) COMP.
       PROCEDURE DIVISION.
           MOVE S TO T
           DISPLAY T
           STOP RUN.
