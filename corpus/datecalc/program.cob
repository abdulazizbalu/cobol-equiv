      * cobol-equiv corpus: DATECALC (MIT licensed)
      * Date arithmetic from input dates, without the system clock.
      * Semantic area: integer DIVIDE ... REMAINDER, leap-year rules,
      * day numbers, a cumulative-days table, conversion back to a
      * calendar date, signed differences.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. DATECALC.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT DATE-FILE ASSIGN TO "DATES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD DATE-FILE.
       01 DATE-REC.
          05 DT-FROM        PIC 9(8).
          05 DT-TO          PIC 9(8).
          05 DT-OFFSET      PIC S9(6).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-CUM-TEXT       PIC X(36)
                  VALUE "000031059090120151181212243273304334".
       01 WS-CUM-TABLE REDEFINES WS-CUM-TEXT.
          05 WS-CUM         PIC 999 OCCURS 12.
       01 WS-DIM-TEXT       PIC X(24)
                  VALUE "312831303130313130313031".
       01 WS-DIM-TABLE REDEFINES WS-DIM-TEXT.
          05 WS-DIM         PIC 99 OCCURS 12.
       01 WS-DOW-TEXT       PIC X(21)
                  VALUE "MONTUEWEDTHUFRISATSUN".
       01 WS-DOW-TABLE REDEFINES WS-DOW-TEXT.
          05 WS-DOW-NAME    PIC X(3) OCCURS 7.
       01 WS-DATE           PIC 9(8).
       01 WS-DATE-R REDEFINES WS-DATE.
          05 WS-YYYY        PIC 9(4).
          05 WS-MM          PIC 99.
          05 WS-DD          PIC 99.
       01 WS-VALID          PIC X.
       01 WS-LEAP           PIC X.
       01 WS-Q              PIC 9(7).
       01 WS-R4             PIC 9(4).
       01 WS-R100           PIC 9(4).
       01 WS-R400           PIC 9(4).
       01 WS-Y              PIC 9(5).
       01 WS-DAYNUM         PIC S9(8).
       01 WS-FROM-NUM       PIC S9(8).
       01 WS-TO-NUM         PIC S9(8).
       01 WS-NEW-NUM        PIC S9(8).
       01 WS-DIFF           PIC S9(8).
       01 WS-DIFF-ED        PIC -(7)9.
       01 WS-DOW-IX         PIC 9.
       01 WS-REM7           PIC 9.
       01 WS-MAXDAY         PIC 99.
       01 WS-RESULT         PIC X(8).
       01 WS-TRY            PIC S9(8).
       01 WS-DONE           PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT DATE-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ DATE-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM DO-PAIR
               END-READ
           END-PERFORM
           CLOSE DATE-FILE
           STOP RUN.

       DO-PAIR.
           MOVE DT-FROM TO WS-DATE
           PERFORM VALIDATE-DATE
           IF WS-VALID = "N"
               DISPLAY DT-FROM " INVALID FROM DATE"
               EXIT PARAGRAPH
           END-IF
           PERFORM DATE-TO-NUM
           MOVE WS-DAYNUM TO WS-FROM-NUM
           MOVE DT-TO TO WS-DATE
           PERFORM VALIDATE-DATE
           IF WS-VALID = "N"
               DISPLAY DT-TO " INVALID TO DATE"
               EXIT PARAGRAPH
           END-IF
           PERFORM DATE-TO-NUM
           MOVE WS-DAYNUM TO WS-TO-NUM
           COMPUTE WS-DIFF = WS-TO-NUM - WS-FROM-NUM
           MOVE WS-DIFF TO WS-DIFF-ED
           DIVIDE WS-FROM-NUM BY 7 GIVING WS-Q REMAINDER WS-REM7
           COMPUTE WS-DOW-IX = WS-REM7 + 1
           COMPUTE WS-NEW-NUM = WS-FROM-NUM + DT-OFFSET
           IF WS-NEW-NUM < 0 OR WS-NEW-NUM > 3067670
               MOVE "RANGE" TO WS-RESULT
           ELSE
               MOVE WS-NEW-NUM TO WS-DAYNUM
               PERFORM NUM-TO-DATE
               MOVE WS-DATE TO WS-RESULT
           END-IF
           DISPLAY DT-FROM " " DT-TO " " WS-DIFF-ED " "
                   WS-DOW-NAME (WS-DOW-IX) " " WS-RESULT.

       VALIDATE-DATE.
           MOVE "Y" TO WS-VALID
           IF WS-YYYY < 1601 OR WS-MM < 1 OR WS-MM > 12 OR WS-DD < 1
               MOVE "N" TO WS-VALID
           ELSE
               PERFORM CHECK-LEAP
               MOVE WS-DIM (WS-MM) TO WS-MAXDAY
               IF WS-MM = 2 AND WS-LEAP = "Y"
                   ADD 1 TO WS-MAXDAY
               END-IF
               IF WS-DD > WS-MAXDAY
                   MOVE "N" TO WS-VALID
               END-IF
           END-IF.

       CHECK-LEAP.
           DIVIDE WS-YYYY BY 4 GIVING WS-Q REMAINDER WS-R4
           DIVIDE WS-YYYY BY 100 GIVING WS-Q REMAINDER WS-R100
           DIVIDE WS-YYYY BY 400 GIVING WS-Q REMAINDER WS-R400
           IF WS-R4 = 0 AND (WS-R100 NOT = 0 OR WS-R400 = 0)
               MOVE "Y" TO WS-LEAP
           ELSE
               MOVE "N" TO WS-LEAP
           END-IF.

      * Days since 1601-01-01 (day 0, a Monday).
       DATE-TO-NUM.
           COMPUTE WS-Y = WS-YYYY - 1601
           DIVIDE WS-Y BY 4 GIVING WS-Q
           COMPUTE WS-DAYNUM = WS-Y * 365 + WS-Q
           DIVIDE WS-Y BY 100 GIVING WS-Q
           SUBTRACT WS-Q FROM WS-DAYNUM
           DIVIDE WS-Y BY 400 GIVING WS-Q
           ADD WS-Q TO WS-DAYNUM
           ADD WS-CUM (WS-MM) WS-DD TO WS-DAYNUM
           SUBTRACT 1 FROM WS-DAYNUM
           PERFORM CHECK-LEAP
           IF WS-LEAP = "Y" AND WS-MM > 2
               ADD 1 TO WS-DAYNUM
           END-IF.

      * Inverse of DATE-TO-NUM. WS-DAYNUM / 366 never overestimates
      * the number of whole years, so only upward steps are needed.
       NUM-TO-DATE.
           MOVE WS-DAYNUM TO WS-TRY
           DIVIDE WS-DAYNUM BY 366 GIVING WS-Y
           COMPUTE WS-YYYY = WS-Y + 1601
           MOVE 1 TO WS-MM WS-DD
           MOVE "N" TO WS-DONE
           PERFORM UNTIL WS-DONE = "Y"
               IF WS-YYYY = 9999
                   MOVE "Y" TO WS-DONE
               ELSE
                   ADD 1 TO WS-YYYY
                   PERFORM DATE-TO-NUM
                   IF WS-DAYNUM > WS-TRY
                       SUBTRACT 1 FROM WS-YYYY
                       MOVE "Y" TO WS-DONE
                   END-IF
               END-IF
           END-PERFORM
           MOVE 12 TO WS-MM
           PERFORM DATE-TO-NUM
           PERFORM UNTIL WS-DAYNUM <= WS-TRY
               SUBTRACT 1 FROM WS-MM
               PERFORM DATE-TO-NUM
           END-PERFORM
           COMPUTE WS-DD = WS-TRY - WS-DAYNUM + 1.
