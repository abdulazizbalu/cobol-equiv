      * cobol-equiv corpus: CUSTLIST (MIT licensed)
      * Customer listing. Semantic area: records with several group
      * levels, MOVE CORRESPONDING between groups of different shape,
      * group moves, REDEFINES of a date group, WRITE FROM.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTLIST.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUST-FILE ASSIGN TO "CUST.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT LIST-FILE ASSIGN TO "CUSTLIST.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CUST-FILE.
       01 CUST-REC.
          05 CU-ID             PIC 9(5).
          05 CU-NAME.
             10 CU-LAST        PIC X(10).
             10 CU-FIRST       PIC X(8).
          05 CU-ADDR.
             10 CU-STREET.
                15 CU-HOUSE    PIC 9(4).
                15 CU-ROAD     PIC X(12).
             10 CU-CITY        PIC X(10).
          05 CU-OPENED.
             10 CU-YYYY        PIC 9(4).
             10 CU-MM          PIC 99.
             10 CU-DD          PIC 99.
          05 CU-OPENED-N REDEFINES CU-OPENED PIC 9(8).
          05 CU-BAL            PIC S9(5)V99.
       FD LIST-FILE.
       01 LIST-REC             PIC X(80).
       WORKING-STORAGE SECTION.
       01 WS-EOF               PIC X VALUE "N".
       01 WS-COUNT             PIC 9(3) VALUE 0.
       01 WS-TOTAL             PIC S9(7)V99 VALUE 0.
       01 WS-OUT-TOTAL         PIC -(7)9.99.
       01 WS-NAME-COPY         PIC X(20).
       01 WS-OUT.
          05 CU-ID             PIC Z(4)9.
          05 FILLER            PIC X VALUE "|".
          05 CU-NAME.
             10 CU-FIRST       PIC X(8).
             10 FILLER         PIC X VALUE SPACE.
             10 CU-LAST        PIC X(10).
          05 FILLER            PIC X VALUE "|".
          05 CU-ADDR.
             10 CU-CITY        PIC X(10).
             10 FILLER         PIC X VALUE ",".
             10 CU-STREET.
                15 CU-HOUSE    PIC ZZZ9.
                15 FILLER      PIC X VALUE SPACE.
                15 CU-ROAD     PIC X(12).
          05 FILLER            PIC X VALUE "|".
          05 WO-DATE.
             10 WO-DD          PIC 99.
             10 FILLER         PIC X VALUE "/".
             10 WO-MM          PIC 99.
             10 FILLER         PIC X VALUE "/".
             10 WO-YYYY        PIC 9(4).
          05 FILLER            PIC X VALUE "|".
          05 CU-BAL            PIC -(5)9.99.
          05 WO-FLAG           PIC X(5).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CUST-FILE OUTPUT LIST-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CUST-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM LIST-CUSTOMER
               END-READ
           END-PERFORM
           CLOSE CUST-FILE LIST-FILE
           MOVE WS-TOTAL TO WS-OUT-TOTAL
           DISPLAY "COUNT " WS-COUNT " TOTAL " WS-OUT-TOTAL
           STOP RUN.

       LIST-CUSTOMER.
           ADD 1 TO WS-COUNT
           ADD CU-BAL OF CUST-REC TO WS-TOTAL
           MOVE CORRESPONDING CUST-REC TO WS-OUT
           MOVE CU-DD TO WO-DD
           MOVE CU-MM TO WO-MM
           MOVE CU-YYYY TO WO-YYYY
           EVALUATE TRUE
               WHEN CU-MM < 1 OR CU-MM > 12
                   MOVE " BADM" TO WO-FLAG
               WHEN CU-OPENED-N < 19000101
                   MOVE " OLD" TO WO-FLAG
               WHEN OTHER
                   MOVE SPACES TO WO-FLAG
           END-EVALUATE
           WRITE LIST-REC FROM WS-OUT
           IF CU-LAST OF CUST-REC = SPACES
               MOVE CU-NAME OF CUST-REC TO WS-NAME-COPY
               DISPLAY "NO LAST NAME " CU-ID OF CUST-REC " ["
                   WS-NAME-COPY "]"
           END-IF.
