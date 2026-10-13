      * cobol-equiv corpus: REDEF (MIT licensed)
      * Variant records selected by a type code. Semantic area:
      * REDEFINES of a record body, nested REDEFINES of a date,
      * a numeric table loaded through REDEFINES of a literal,
      * trailer checks with signed totals.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. REDEF.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT REC-FILE ASSIGN TO "RECS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD REC-FILE.
       01 IN-REC.
          05 IR-TYPE        PIC X.
          05 IR-BODY        PIC X(29).
          05 IR-HEADER REDEFINES IR-BODY.
             10 IH-NAME     PIC X(20).
             10 IH-DATE     PIC 9(8).
             10 IH-DATE-R REDEFINES IH-DATE.
                15 IH-YYYY  PIC 9(4).
                15 IH-MM    PIC 99.
                15 IH-DD    PIC 99.
             10 FILLER      PIC X.
          05 IR-DETAIL REDEFINES IR-BODY.
             10 ID-ITEM     PIC X(5).
             10 ID-QTY      PIC S9(4).
             10 ID-PRICE    PIC 9(5)V99.
             10 ID-DISC     PIC V99.
             10 FILLER      PIC X(11).
          05 IR-TRAILER REDEFINES IR-BODY.
             10 IT-COUNT    PIC 9(5).
             10 IT-TOTAL    PIC S9(9)V99.
             10 FILLER      PIC X(13).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-DAYS-TEXT      PIC X(24)
                            VALUE "312931303130313130313031".
       01 WS-DAYS-TABLE REDEFINES WS-DAYS-TEXT.
          05 WS-DAYS        PIC 99 OCCURS 12.
       01 WS-RUN-COUNT      PIC 9(5) VALUE 0.
       01 WS-RUN-TOTAL      PIC S9(9)V99 VALUE 0.
       01 WS-LINE-AMT       PIC S9(9)V99.
       01 WS-LINE-ED        PIC ---,---,--9.99.
       01 WS-DATE-OK        PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT REC-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ REC-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM DO-RECORD
               END-READ
           END-PERFORM
           CLOSE REC-FILE
           DISPLAY "OPEN COUNT " WS-RUN-COUNT " TOTAL " WS-RUN-TOTAL
           STOP RUN.

       DO-RECORD.
           EVALUATE IR-TYPE
               WHEN "H"
                   PERFORM DO-HEADER
               WHEN "D"
                   PERFORM DO-DETAIL
               WHEN "T"
                   PERFORM DO-TRAILER
               WHEN OTHER
                   DISPLAY "UNKNOWN TYPE " IR-TYPE
           END-EVALUATE.

       DO-HEADER.
           MOVE "Y" TO WS-DATE-OK
           IF IH-MM < 1 OR IH-MM > 12
               MOVE "N" TO WS-DATE-OK
           ELSE
               IF IH-DD < 1 OR IH-DD > WS-DAYS (IH-MM)
                   MOVE "N" TO WS-DATE-OK
               END-IF
           END-IF
           DISPLAY "HEADER " IH-NAME " " IH-YYYY "-" IH-MM "-" IH-DD
                   " " WS-DATE-OK " " IH-DATE.

       DO-DETAIL.
           COMPUTE WS-LINE-AMT ROUNDED =
               ID-QTY * ID-PRICE * (1 - ID-DISC)
           MOVE WS-LINE-AMT TO WS-LINE-ED
           ADD 1 TO WS-RUN-COUNT
           ADD WS-LINE-AMT TO WS-RUN-TOTAL
           DISPLAY "DETAIL " ID-ITEM " " WS-LINE-ED.

       DO-TRAILER.
           IF IT-COUNT = WS-RUN-COUNT AND IT-TOTAL = WS-RUN-TOTAL
               DISPLAY "TRAILER OK " IT-COUNT
           ELSE
               DISPLAY "TRAILER MISMATCH " IT-COUNT " " IT-TOTAL
                       " " WS-RUN-COUNT " " WS-RUN-TOTAL
           END-IF
           MOVE 0 TO WS-RUN-COUNT WS-RUN-TOTAL.
