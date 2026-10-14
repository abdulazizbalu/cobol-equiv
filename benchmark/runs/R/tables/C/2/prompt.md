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
input_files = {'ITEMS.DAT': b'AAA00000000\n'}
expected stdout = b' 1 AAA      0       0.00\nITEMS 01 REJECTED 00\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'ITEMS.DAT': b'JJJ00000000\n'}
expected stdout = b' 1 JJJ      0       0.00\nITEMS 01 REJECTED 00\n'
expected output_files = {}

## COBOL program
```cobol
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
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
