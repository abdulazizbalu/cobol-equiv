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
input_files = {'CUST.DAT': b'00000                  0000                      00000000000000p\n'}
expected stdout = b'NO LAST NAME 00000 [                    ]\nCOUNT 001 TOTAL        0.00\n'
expected output_files = {'CUSTLIST.DAT': b'    0|                   |          ,   0             |00/00/0000|     0.00 BADM\n'}

### Example 2
stdin = b''
input_files = {'CUST.DAT': b'00729g+GCac=r  .*/dL<Mo0649                      74911298000010p\n00315353       O{f=IBJ 9998$4          hmu3)30Wxl000102990065536\n99998~y:|y*NeFcvd `95jW999989          Ws>m      000304050165583\n'}
expected stdout = b'COUNT 003 TOTAL     2310.19\n'
expected output_files = {'CUSTLIST.DAT': b'  729|.*/dL<Mo g+GCac=r  |          , 649             |98/12/7491|    -1.00\n  315|O{f=IBJ  353       |hmu3)30Wxl,9998 $4          |99/02/0001|   655.36 OLD\n99998|vd `95jW ~y:|y*NeFc|Ws>m      ,9999 89          |05/04/0003|  1655.83 OLD\n'}

## COBOL program
```cobol
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
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
