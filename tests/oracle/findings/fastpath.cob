      * Finding: single-operand ADD / SUBTRACT integer path.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. FASTP.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 U          PIC 9(4) COMP-5 VALUE 0.
       01 GP.
          05 P       PIC 9(4) COMP-3 VALUE 9999.
       01 HEXP       PIC X(6).
       01 I          PIC 9.
       01 V          PIC 999.
       01 H          PIC 99.
       01 L          PIC 99.
       01 DIG        PIC X(16) VALUE "0123456789ABCDEF".
       PROCEDURE DIVISION.
           SUBTRACT 1 FROM U
           DISPLAY "SUBTRACT 1 FROM 0 9(4) COMP-5: " U
           ADD 1 TO P
           PERFORM VARYING I FROM 1 BY 1 UNTIL I > 3
               COMPUTE V = FUNCTION ORD(GP(I:1)) - 1
               DIVIDE V BY 16 GIVING H REMAINDER L
               MOVE DIG(H + 1:1) TO HEXP(2 * I - 1:1)
               MOVE DIG(L + 1:1) TO HEXP(2 * I:1)
           END-PERFORM
           DISPLAY "ADD 1 TO 9999 9(4) COMP-3: x'" HEXP "'"
           STOP RUN.
