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
input_files = {'SHIPS.DAT': b'AAE000000\n'}
expected stdout = b'AAE 00 x 000.0 =         0.00\nPRICED 001 MISSING 000 TOTAL          0.00\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'SHIPS.DAT': b'ABE000000\n'}
expected stdout = b'NO RATE AB/E\nPRICED 000 MISSING 001 TOTAL          0.00\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. RATELOOK.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SHIP-FILE ASSIGN TO "SHIPS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD SHIP-FILE.
       01 SHIP-REC.
          05 SH-ZONE        PIC X(2).
          05 SH-CLASS       PIC X.
          05 SH-WEIGHT      PIC 9(3)V9.
          05 SH-QTY         PIC 99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 RATE-DATA.
          05 FILLER PIC X(13) VALUE "AAE0450001250".
          05 FILLER PIC X(13) VALUE "AAS0300000800".
          05 FILLER PIC X(13) VALUE "BKE0600001575".
          05 FILLER PIC X(13) VALUE "BKS0420001010".
          05 FILLER PIC X(13) VALUE "CNE0725002030".
          05 FILLER PIC X(13) VALUE "CNS0510001333".
          05 FILLER PIC X(13) VALUE "DEE0999002500".
          05 FILLER PIC X(13) VALUE "DES0650001725".
          05 FILLER PIC X(13) VALUE "FRE0880002200".
          05 FILLER PIC X(13) VALUE "FRS0600001480".
          05 FILLER PIC X(13) VALUE "UZE1200003125".
          05 FILLER PIC X(13) VALUE "UZS0875002250".
       01 RATE-TABLE REDEFINES RATE-DATA.
          05 RT-ENTRY OCCURS 12 TIMES
                ASCENDING KEY IS RT-ZONE RT-CLASS
                INDEXED BY RX.
             10 RT-ZONE     PIC X(2).
             10 RT-CLASS    PIC X.
             10 RT-BASE     PIC 9(3)V99.
             10 RT-PER-KG   PIC 9(3)V99.
       01 WS-CHARGE         PIC 9(7)V99.
       01 WS-TOTAL          PIC 9(8)V99 VALUE 0.
       01 WS-FOUND          PIC 9(3) VALUE 0.
       01 WS-MISSING        PIC 9(3) VALUE 0.
       01 WS-OUT-CHARGE     PIC Z,ZZZ,ZZ9.99.
       01 WS-OUT-TOTAL      PIC ZZ,ZZZ,ZZ9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT SHIP-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ SHIP-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PRICE-SHIPMENT
               END-READ
           END-PERFORM
           CLOSE SHIP-FILE
           MOVE WS-TOTAL TO WS-OUT-TOTAL
           DISPLAY "PRICED " WS-FOUND " MISSING " WS-MISSING
               " TOTAL " WS-OUT-TOTAL
           STOP RUN.

       PRICE-SHIPMENT.
           SEARCH ALL RT-ENTRY
               AT END
                   ADD 1 TO WS-MISSING
                   DISPLAY "NO RATE " SH-ZONE "/" SH-CLASS
               WHEN RT-ZONE (RX) = SH-ZONE AND RT-CLASS (RX) = SH-CLASS
                   ADD 1 TO WS-FOUND
                   COMPUTE WS-CHARGE ROUNDED =
                       (RT-BASE (RX) + RT-PER-KG (RX) * SH-WEIGHT)
                       * SH-QTY * (100 - SH-QTY / 4) / 100
                   ADD WS-CHARGE TO WS-TOTAL
                   MOVE WS-CHARGE TO WS-OUT-CHARGE
                   DISPLAY SH-ZONE SH-CLASS " " SH-QTY " x " SH-WEIGHT
                       " = " WS-OUT-CHARGE
           END-SEARCH.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
