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
input_files = {'EMPLOYEES.DAT': b'E0000          000000000A000000p\n'}
expected stdout = b'E0000            +0000000.00 +0000000.00 +00050.00 -0000050.00\nEMPLOYEES 001\nTOTAL GROSS +000000000.00\nTOTAL NET   -000000050.00\nNEGATIVE NET 001\n'
expected output_files = {'PAYOUT.DAT': b'E0000\x00\x00\x00\x00\x0c\x00\x00\x05\x00\r00000500pN'}

### Example 2
stdin = b''
input_files = {'EMPLOYEES.DAT': b'E4000          000000000A000000p\n'}
expected stdout = b'E4000            +0000000.00 +0000000.00 +00050.00 -0000050.00\nEMPLOYEES 001\nTOTAL GROSS +000000000.00\nTOTAL NET   -000000050.00\nNEGATIVE NET 001\n'
expected output_files = {'PAYOUT.DAT': b'E4000\x00\x00\x00\x00\x0c\x00\x00\x05\x00\r00000500pN'}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYROLL.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMP-FILE ASSIGN TO "EMPLOYEES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT PAY-FILE ASSIGN TO "PAYOUT.DAT"
               ORGANIZATION IS SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD EMP-FILE.
       01 EMP-REC.
          05 EMP-ID         PIC X(5).
          05 EMP-NAME       PIC X(10).
          05 EMP-HOURS      PIC 9(3)V9.
          05 EMP-RATE       PIC 9(3)V99.
          05 EMP-DED-CODE   PIC X.
          05 EMP-ADJUST     PIC S9(5)V99.
       FD PAY-FILE.
       01 PAY-REC.
          05 PAY-ID         PIC X(5).
          05 PAY-GROSS      PIC S9(7)V99 COMP-3.
          05 PAY-NET        PIC S9(7)V99 COMP-3.
          05 PAY-NET-D      PIC S9(7)V99.
          05 PAY-FLAG       PIC X.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-OT-HOURS       PIC S9(3)V9 COMP-3.
       01 WS-GROSS          PIC S9(7)V99 COMP-3.
       01 WS-TAX            PIC S9(7)V99 COMP-3.
       01 WS-DED            PIC S9(5)V99 COMP-3.
       01 WS-NET            PIC S9(7)V99 COMP-3.
       01 WS-TOT-GROSS      PIC S9(9)V99 COMP-3 VALUE 0.
       01 WS-TOT-NET        PIC S9(9)V99 COMP-3 VALUE 0.
       01 WS-NEG-COUNT      PIC 9(3) COMP-3 VALUE 0.
       01 WS-EMP-COUNT      PIC 9(3) COMP-3 VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT EMP-FILE OUTPUT PAY-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ EMP-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PAY-ONE
               END-READ
           END-PERFORM
           CLOSE EMP-FILE PAY-FILE
           DISPLAY "EMPLOYEES " WS-EMP-COUNT
           DISPLAY "TOTAL GROSS " WS-TOT-GROSS
           DISPLAY "TOTAL NET   " WS-TOT-NET
           DISPLAY "NEGATIVE NET " WS-NEG-COUNT
           STOP RUN.

       PAY-ONE.
           ADD 1 TO WS-EMP-COUNT
           IF EMP-HOURS > 40
               COMPUTE WS-OT-HOURS = EMP-HOURS - 40
               COMPUTE WS-GROSS ROUNDED =
                   40 * EMP-RATE + WS-OT-HOURS * EMP-RATE * 1.5
           ELSE
               MOVE 0 TO WS-OT-HOURS
               COMPUTE WS-GROSS ROUNDED = EMP-HOURS * EMP-RATE
           END-IF
           EVALUATE TRUE
               WHEN WS-GROSS <= 1000
                   COMPUTE WS-TAX ROUNDED = WS-GROSS * 0.10
               WHEN WS-GROSS <= 5000
                   COMPUTE WS-TAX ROUNDED =
                       100 + (WS-GROSS - 1000) * 0.25
               WHEN OTHER
                   COMPUTE WS-TAX ROUNDED =
                       1100 + (WS-GROSS - 5000) * 0.35
           END-EVALUATE
           EVALUATE EMP-DED-CODE
               WHEN "A"
                   MOVE 50 TO WS-DED
               WHEN "B"
                   COMPUTE WS-DED ROUNDED = WS-GROSS * 0.045
               WHEN "C"
                   MOVE 0 TO WS-DED
               WHEN OTHER
                   MOVE 25.50 TO WS-DED
           END-EVALUATE
           COMPUTE WS-NET = WS-GROSS - WS-TAX - WS-DED + EMP-ADJUST
           MOVE SPACE TO PAY-FLAG
           IF WS-NET < 0
               ADD 1 TO WS-NEG-COUNT
               MOVE "N" TO PAY-FLAG
           END-IF
           ADD WS-GROSS TO WS-TOT-GROSS
           ADD WS-NET TO WS-TOT-NET
           MOVE EMP-ID TO PAY-ID
           MOVE WS-GROSS TO PAY-GROSS
           MOVE WS-NET TO PAY-NET
           MOVE WS-NET TO PAY-NET-D
           WRITE PAY-REC
           DISPLAY EMP-ID " " EMP-NAME " " WS-GROSS " " WS-TAX " "
               WS-DED " " WS-NET.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
