      * cobol-equiv corpus: CLASSIFY (MIT licensed)
      * Customer classification. Semantic area: EVALUATE TRUE,
      * EVALUATE ... ALSO with ANY and THRU, nested IF with AND, OR,
      * NOT, algebraic comparison of signed numbers.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CLASSIFY.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUST-FILE ASSIGN TO "CUST.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CUST-FILE.
       01 CUST-REC.
          05 CU-ID          PIC X(4).
          05 CU-TYPE        PIC X.
          05 CU-AGE         PIC 9(3).
          05 CU-BALANCE     PIC S9(7)V99.
          05 CU-DAYS-LATE   PIC 9(3).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-CLASS          PIC X(7).
       01 WS-SEGMENT        PIC X(10).
       01 WS-AGEBAND        PIC X(6).
       01 WS-RISK           PIC 9.
       01 WS-COUNTS.
          05 WS-CNT-CREDIT  PIC 9(3) VALUE 0.
          05 WS-CNT-DEFAULT PIC 9(3) VALUE 0.
          05 WS-CNT-WATCH   PIC 9(3) VALUE 0.
          05 WS-CNT-NORMAL  PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CUST-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CUST-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM CLASSIFY-ONE
               END-READ
           END-PERFORM
           CLOSE CUST-FILE
           DISPLAY "CREDIT " WS-CNT-CREDIT " DEFAULT " WS-CNT-DEFAULT
                   " WATCH " WS-CNT-WATCH " NORMAL " WS-CNT-NORMAL
           STOP RUN.

       CLASSIFY-ONE.
           EVALUATE TRUE
               WHEN CU-BALANCE < 0
                   MOVE "CREDIT" TO WS-CLASS
                   ADD 1 TO WS-CNT-CREDIT
               WHEN CU-DAYS-LATE > 90
                   MOVE "DEFAULT" TO WS-CLASS
                   ADD 1 TO WS-CNT-DEFAULT
               WHEN CU-DAYS-LATE > 30 AND CU-BALANCE > 1000
                   MOVE "WATCH" TO WS-CLASS
                   ADD 1 TO WS-CNT-WATCH
               WHEN OTHER
                   MOVE "NORMAL" TO WS-CLASS
                   ADD 1 TO WS-CNT-NORMAL
           END-EVALUATE
           EVALUATE CU-TYPE ALSO TRUE
               WHEN "P" ALSO CU-AGE < 25
                   MOVE "YOUNG-P" TO WS-SEGMENT
               WHEN "P" ALSO CU-AGE >= 65
                   MOVE "SENIOR-P" TO WS-SEGMENT
               WHEN "P" ALSO ANY
                   MOVE "PERSONAL" TO WS-SEGMENT
               WHEN "B" ALSO ANY
                   MOVE "BUSINESS" TO WS-SEGMENT
               WHEN "G" THRU "J" ALSO ANY
                   MOVE "PUBLIC" TO WS-SEGMENT
               WHEN OTHER
                   MOVE "UNKNOWN" TO WS-SEGMENT
           END-EVALUATE
           IF CU-TYPE = "B"
               IF CU-BALANCE > 50000 OR CU-DAYS-LATE > 60
                   MOVE 3 TO WS-RISK
               ELSE
                   IF CU-BALANCE > 10000
                       MOVE 2 TO WS-RISK
                   ELSE
                       MOVE 1 TO WS-RISK
                   END-IF
               END-IF
           ELSE
               IF CU-DAYS-LATE = 0 AND NOT CU-BALANCE < 0
                   MOVE 0 TO WS-RISK
               ELSE
                   IF CU-DAYS-LATE > 30 OR CU-BALANCE < -500
                       MOVE 2 TO WS-RISK
                   ELSE
                       MOVE 1 TO WS-RISK
                   END-IF
               END-IF
           END-IF
           EVALUATE CU-AGE
               WHEN 0 THRU 17
                   MOVE "MINOR" TO WS-AGEBAND
               WHEN 18 THRU 64
                   MOVE "ADULT" TO WS-AGEBAND
               WHEN OTHER
                   MOVE "SENIOR" TO WS-AGEBAND
           END-EVALUATE
           DISPLAY CU-ID " " WS-CLASS " " WS-SEGMENT " " WS-RISK " "
                   WS-AGEBAND.
