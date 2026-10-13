      * Finding: negative zero after high-order truncation.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. NEGZERO.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 S          PIC S9(6) VALUE -10000.
       01 GD.
          05 D       PIC S9(4).
       01 GP.
          05 P       PIC S9(5) COMP-3.
       01 GM.
          05 M       PIC S9(4).
       01 S2         PIC S9(7) VALUE -100000.
       01 HEXP       PIC X(6).
       01 I          PIC 9.
       01 V          PIC 999.
       01 H          PIC 99.
       01 L          PIC 99.
       01 DIG        PIC X(16) VALUE "0123456789ABCDEF".
       PROCEDURE DIVISION.
           MOVE S TO D
           DISPLAY "MOVE-DISPLAY [" GD "] " D
           ADD S2 TO P
           PERFORM VARYING I FROM 1 BY 1 UNTIL I > 3
               COMPUTE V = FUNCTION ORD(GP(I:1)) - 1
               DIVIDE V BY 16 GIVING H REMAINDER L
               MOVE DIG(H + 1:1) TO HEXP(2 * I - 1:1)
               MOVE DIG(L + 1:1) TO HEXP(2 * I:1)
           END-PERFORM
           DISPLAY "ADD-COMP3 x'" HEXP "' " P
           ADD S TO M
           DISPLAY "ADD-DISPLAY [" GM "] " M
           IF D = 0 DISPLAY "D-EQUALS-ZERO" END-IF
           STOP RUN.
