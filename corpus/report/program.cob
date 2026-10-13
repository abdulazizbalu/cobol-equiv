      * cobol-equiv corpus: REPORT (MIT licensed)
      * Report lines with numeric editing. Semantic area: Z, *, $,
      * floating and fixed signs, CR/DB, insertion characters, and
      * high-order truncation when a value is wider than its picture.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. REPORT1.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT AMT-FILE ASSIGN TO "AMOUNTS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT RPT-FILE ASSIGN TO "REPORT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD AMT-FILE.
       01 AMT-REC.
          05 AM-LABEL       PIC X(6).
          05 AM-VALUE       PIC S9(7)V99.
          05 AM-DATE        PIC 9(6).
          05 AM-QTY         PIC S9(4).
       FD RPT-FILE.
       01 RPT-REC           PIC X(80).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-TOTAL          PIC S9(9)V99 VALUE 0.
       01 WS-QTY-TOTAL      PIC S9(6) VALUE 0.
       01 LINE-1.
          05 L1-LABEL       PIC X(6).
          05 FILLER         PIC X VALUE SPACE.
          05 L1-A           PIC ZZZ,ZZ9.99-.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-B           PIC $$$,$$$,$$9.99CR.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-C           PIC ***,***,**9.99.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-D           PIC +ZZZ9.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-E           PIC 99/99/99.
          05 FILLER         PIC X VALUE SPACE.
          05 L1-F           PIC ---,--9.
       01 LINE-2.
          05 FILLER         PIC X(7) VALUE "       ".
          05 L2-G           PIC Z(4)9.999.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-H           PIC 999B999.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-I           PIC $ZZ,ZZ9.99DB.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-J           PIC ZZ9.9+.
          05 FILLER         PIC X VALUE SPACE.
          05 L2-K           PIC ZZZZ.
       01 TOTAL-LINE.
          05 FILLER         PIC X(7) VALUE "TOTAL  ".
          05 TL-AMOUNT      PIC $$$$,$$$,$$9.99CR.
          05 FILLER         PIC X(5) VALUE " QTY ".
          05 TL-QTY         PIC ---,--9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT AMT-FILE OUTPUT RPT-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ AMT-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM REPORT-ONE
               END-READ
           END-PERFORM
           MOVE WS-TOTAL TO TL-AMOUNT
           MOVE WS-QTY-TOTAL TO TL-QTY
           WRITE RPT-REC FROM TOTAL-LINE
           CLOSE AMT-FILE RPT-FILE
           STOP RUN.

       REPORT-ONE.
           MOVE AM-LABEL TO L1-LABEL
           MOVE AM-VALUE TO L1-A L1-B L1-C L2-G L2-I L2-J
           MOVE AM-QTY TO L1-D L1-F L2-K
           MOVE AM-DATE TO L1-E L2-H
           WRITE RPT-REC FROM LINE-1
           WRITE RPT-REC FROM LINE-2
           ADD AM-VALUE TO WS-TOTAL
           ADD AM-QTY TO WS-QTY-TOTAL.
