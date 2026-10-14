Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

Use only the Python standard library. The module runs in an interpreter
that has no other packages.

## IO contract
The Python module must define

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]

- stdin: everything the program reads with ACCEPT (one ACCEPT reads one line).
- input_files: for every file the program reads, the name in its ASSIGN
  clause mapped to the full content of the file. LINE SEQUENTIAL files are
  lines that end with "\n"; SEQUENTIAL files are fixed-length records
  without separators.
- The return value is all bytes the program writes to standard output, and
  a dict that maps the ASSIGN name of every file the program opens for
  output to the full content of that file.
- The module must not read the clock, random sources, the network or the
  file system, and must not start processes. It runs on Python 3.12.

## Examples
These are inputs and the exact outputs of the COBOL program.
### Example 1
stdin = b''
input_files = {'CELLS.DAT': b'00=00p\n'}
expected stdout = b'    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\nCOL 1     0\nCOL 2     0\nCOL 3     0\nCOL 4     0\nCOL 5     0\nMAX +0000 AT 1,1 BAD 01\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'CELLS.DAT': b'30=00p\n'}
expected stdout = b'    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\n    0     0     0     0     0           =     0\nCOL 1     0\nCOL 2     0\nCOL 3     0\nCOL 4     0\nCOL 5     0\nMAX +0000 AT 1,1 BAD 01\n'
expected output_files = {}

## COBOL program
```cobol
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
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
