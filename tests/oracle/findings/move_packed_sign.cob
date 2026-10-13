      * Finding: MOVE unsigned COMP-3 to signed COMP-3 (ticket #904).
       IDENTIFICATION DIVISION.
       PROGRAM-ID. MVPK.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 U          PIC 9(3) COMP-3 VALUE 51.
       01 GS.
          05 S       PIC S9(3) COMP-3.
       01 HEXS       PIC X(4).
       01 I          PIC 9.
       01 V          PIC 999.
       01 H          PIC 99.
       01 L          PIC 99.
       01 DIG        PIC X(16) VALUE "0123456789ABCDEF".
       PROCEDURE DIVISION.
           MOVE U TO S
           PERFORM VARYING I FROM 1 BY 1 UNTIL I > 2
               COMPUTE V = FUNCTION ORD(GS(I:1)) - 1
               DIVIDE V BY 16 GIVING H REMAINDER L
               MOVE DIG(H + 1:1) TO HEXS(2 * I - 1:1)
               MOVE DIG(L + 1:1) TO HEXS(2 * I:1)
           END-PERFORM
           DISPLAY "x'" HEXS "'"
           IF S IS NUMERIC DISPLAY "NUMERIC" ELSE DISPLAY "NOT NUMERIC"
           END-IF
           STOP RUN.
