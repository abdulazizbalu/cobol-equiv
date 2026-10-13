      * cobol-equiv corpus: TABLES (MIT licensed)
      * Item totals in an OCCURS table. Semantic area: OCCURS with
      * INDEXED BY, SEARCH, PERFORM VARYING ... AFTER, group moves for
      * swapping, high-order truncation of an accumulating item.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TABLES.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ITEM-FILE ASSIGN TO "ITEMS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD ITEM-FILE.
       01 ITEM-REC.
          05 IT-CODE        PIC X(3).
          05 IT-QTY         PIC 9(3).
          05 IT-PRICE       PIC 9(3)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-TABLE.
          05 WS-ENTRY OCCURS 8 TIMES INDEXED BY TX.
             10 WS-CODE     PIC X(3).
             10 WS-QTY      PIC 9(5).
             10 WS-AMT      PIC 9(6)V99.
       01 WS-SWAP           PIC X(16).
       01 WS-COUNT          PIC 99 VALUE 0.
       01 WS-REJECTED       PIC 99 VALUE 0.
       01 WS-I              PIC 99.
       01 WS-J              PIC 99.
       01 WS-LINE.
          05 WL-RANK        PIC Z9.
          05 FILLER         PIC X VALUE SPACE.
          05 WL-CODE        PIC X(3).
          05 FILLER         PIC X VALUE SPACE.
          05 WL-QTY         PIC ZZ,ZZ9.
          05 FILLER         PIC X VALUE SPACE.
          05 WL-AMT         PIC ZZZ,ZZ9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT ITEM-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ ITEM-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM ADD-ITEM
               END-READ
           END-PERFORM
           CLOSE ITEM-FILE
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I >= WS-COUNT
               AFTER WS-J FROM 1 BY 1 UNTIL WS-J > WS-COUNT - WS-I
               IF WS-AMT (WS-J) < WS-AMT (WS-J + 1)
                   MOVE WS-ENTRY (WS-J) TO WS-SWAP
                   MOVE WS-ENTRY (WS-J + 1) TO WS-ENTRY (WS-J)
                   MOVE WS-SWAP TO WS-ENTRY (WS-J + 1)
               END-IF
           END-PERFORM
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-COUNT
               MOVE WS-I TO WL-RANK
               MOVE WS-CODE (WS-I) TO WL-CODE
               MOVE WS-QTY (WS-I) TO WL-QTY
               MOVE WS-AMT (WS-I) TO WL-AMT
               DISPLAY WS-LINE
           END-PERFORM
           DISPLAY "ITEMS " WS-COUNT " REJECTED " WS-REJECTED
           STOP RUN.

       ADD-ITEM.
           SET TX TO 1
           SEARCH WS-ENTRY
               AT END
                   PERFORM NEW-ENTRY
               WHEN WS-CODE (TX) = IT-CODE
                   ADD IT-QTY TO WS-QTY (TX)
                   COMPUTE WS-AMT (TX) = WS-AMT (TX) + IT-QTY * IT-PRICE
           END-SEARCH.

       NEW-ENTRY.
           IF WS-COUNT < 8
               ADD 1 TO WS-COUNT
               MOVE IT-CODE TO WS-CODE (WS-COUNT)
               MOVE IT-QTY TO WS-QTY (WS-COUNT)
               COMPUTE WS-AMT (WS-COUNT) = IT-QTY * IT-PRICE
           ELSE
               ADD 1 TO WS-REJECTED
               DISPLAY "TABLE FULL " IT-CODE
           END-IF.
