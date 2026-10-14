      * cobol-equiv corpus: MATRIX (MIT licensed)
      * A 4 x 5 matrix filled from cell records. Semantic area: two-level
      * OCCURS, PERFORM VARYING ... AFTER, nested out-of-line and inline
      * PERFORMs, transposition, row and column sums.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. MATRIX.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CELL-FILE ASSIGN TO "CELLS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD CELL-FILE.
       01 CELL-REC.
          05 CL-ROW         PIC 9.
          05 CL-COL         PIC 9.
          05 CL-OP          PIC X.
          05 CL-VAL         PIC S9(3).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-MATRIX.
          05 WS-ROW OCCURS 4 TIMES.
             10 WS-CELL     PIC S9(4) OCCURS 5 TIMES.
       01 WS-TRANS.
          05 WT-ROW OCCURS 5 TIMES.
             10 WT-CELL     PIC S9(4) OCCURS 4 TIMES.
       01 WS-I              PIC 9.
       01 WS-J              PIC 9.
       01 WS-SUM            PIC S9(5).
       01 WS-MAX            PIC S9(4).
       01 WS-MAX-I          PIC 9.
       01 WS-MAX-J          PIC 9.
       01 WS-BAD            PIC 99 VALUE 0.
       01 WS-LINE           PIC X(40).
       01 WS-PTR            PIC 99.
       01 WS-ED             PIC -(4)9.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CELL-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ CELL-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM APPLY-CELL
               END-READ
           END-PERFORM
           CLOSE CELL-FILE
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 4
                   AFTER WS-J FROM 1 BY 1 UNTIL WS-J > 5
               MOVE WS-CELL (WS-I WS-J) TO WT-CELL (WS-J WS-I)
           END-PERFORM
           MOVE WS-CELL (1 1) TO WS-MAX
           MOVE 1 TO WS-MAX-I WS-MAX-J
           PERFORM PRINT-ROW VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 4
           PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 5
               MOVE 0 TO WS-SUM
               PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 4
                   ADD WT-CELL (WS-J WS-I) TO WS-SUM
               END-PERFORM
               MOVE WS-SUM TO WS-ED
               DISPLAY "COL " WS-J " " WS-ED
           END-PERFORM
           DISPLAY "MAX " WS-MAX " AT " WS-MAX-I "," WS-MAX-J
               " BAD " WS-BAD
           STOP RUN.

       APPLY-CELL.
           IF CL-ROW < 1 OR CL-ROW > 4 OR CL-COL < 1 OR CL-COL > 5
               ADD 1 TO WS-BAD
           ELSE
               EVALUATE CL-OP
                   WHEN "="
                       MOVE CL-VAL TO WS-CELL (CL-ROW CL-COL)
                   WHEN "+"
                       ADD CL-VAL TO WS-CELL (CL-ROW CL-COL)
                   WHEN "*"
                       MULTIPLY CL-VAL BY WS-CELL (CL-ROW CL-COL)
                   WHEN OTHER
                       ADD 1 TO WS-BAD
               END-EVALUATE
           END-IF.

       PRINT-ROW.
           MOVE SPACES TO WS-LINE
           MOVE 1 TO WS-PTR
           MOVE 0 TO WS-SUM
           PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 5
               PERFORM CHECK-MAX
               ADD WS-CELL (WS-I WS-J) TO WS-SUM
               MOVE WS-CELL (WS-I WS-J) TO WS-ED
               STRING WS-ED DELIMITED BY SIZE
                   " " DELIMITED BY SIZE
                   INTO WS-LINE WITH POINTER WS-PTR
           END-PERFORM
           MOVE WS-SUM TO WS-ED
           DISPLAY WS-LINE "= " WS-ED.

       CHECK-MAX.
           IF WS-CELL (WS-I WS-J) > WS-MAX
               MOVE WS-CELL (WS-I WS-J) TO WS-MAX
               MOVE WS-I TO WS-MAX-I
               MOVE WS-J TO WS-MAX-J
           END-IF.
