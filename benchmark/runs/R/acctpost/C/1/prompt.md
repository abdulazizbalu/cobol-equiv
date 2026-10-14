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
input_files = {'TXNS.DAT': b'A00100000000\n'}
expected stdout = b'REJECT A001 0     0.00 BAD TYPE            \nA001        0.00 000\nERRORS 001\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'TXNS.DAT': b'B00230000080\nD00140000543\nC00140000005\nA00240383006\n'}
expected stdout = b'FEE B002     0.26\nREJECT D001 4     5.43 BAD TYPE            \nREJECT C001 4     0.05 BAD TYPE            \nREJECT A002 4  3830.06 BAD TYPE            \nB002       -0.26 001\nD001        0.00 000\nC001        0.00 000\nA002        0.00 000\nERRORS 003\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTPOST.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TXN-FILE ASSIGN TO "TXNS.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD TXN-FILE.
       01 TXN-REC.
          05 TX-ACCT        PIC X(4).
          05 TX-TYPE        PIC 9.
          05 TX-AMT         PIC 9(5)V99.
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-ACCOUNTS.
          05 WS-ACC OCCURS 5 TIMES.
             10 WS-ACC-ID   PIC X(4).
             10 WS-BAL      PIC S9(7)V99.
             10 WS-NTX      PIC 9(3).
       01 WS-NACC           PIC 9 VALUE 0.
       01 WS-I              PIC 9.
       01 WS-K              PIC 9.
       01 WS-FEE            PIC 9(3)V99.
       01 WS-ERRORS         PIC 9(3) VALUE 0.
       01 WS-MSG            PIC X(20).
       01 WS-OUT-BAL        PIC -(7)9.99.
       01 WS-OUT-AMT        PIC Z(4)9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT TXN-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ TXN-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM POST-TXN THRU POST-EXIT
               END-READ
           END-PERFORM
           CLOSE TXN-FILE
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-NACC
               MOVE WS-BAL (WS-I) TO WS-OUT-BAL
               DISPLAY WS-ACC-ID (WS-I) " " WS-OUT-BAL " " WS-NTX (WS-I)
           END-PERFORM
           DISPLAY "ERRORS " WS-ERRORS
           STOP RUN.

       POST-TXN.
           IF TX-ACCT = SPACES
               MOVE "NO ACCOUNT" TO WS-MSG
               GO TO POST-ERROR
           END-IF
           PERFORM FIND-ACCOUNT
           IF WS-K = 0
               MOVE "TOO MANY ACCOUNTS" TO WS-MSG
               GO TO POST-ERROR
           END-IF
           GO TO DO-DEPOSIT DO-WITHDRAW DO-FEE DEPENDING ON TX-TYPE
           MOVE "BAD TYPE" TO WS-MSG
           GO TO POST-ERROR.
       DO-DEPOSIT.
           ADD TX-AMT TO WS-BAL (WS-K)
           GO TO POST-COUNT.
       DO-WITHDRAW.
           IF TX-AMT > WS-BAL (WS-K)
               MOVE "INSUFFICIENT FUNDS" TO WS-MSG
               GO TO POST-ERROR
           END-IF
           SUBTRACT TX-AMT FROM WS-BAL (WS-K)
           GO TO POST-COUNT.
       DO-FEE.
           COMPUTE WS-FEE ROUNDED = TX-AMT * 0.015 + 0.25
           SUBTRACT WS-FEE FROM WS-BAL (WS-K)
           MOVE WS-FEE TO WS-OUT-AMT
           DISPLAY "FEE " TX-ACCT " " WS-OUT-AMT.
       POST-COUNT.
           ADD 1 TO WS-NTX (WS-K)
           GO TO POST-EXIT.
       POST-ERROR.
           ADD 1 TO WS-ERRORS
           MOVE TX-AMT TO WS-OUT-AMT
           DISPLAY "REJECT " TX-ACCT " " TX-TYPE " " WS-OUT-AMT " "
               WS-MSG.
       POST-EXIT.
           EXIT.

       FIND-ACCOUNT.
           MOVE 0 TO WS-K
           PERFORM VARYING WS-I FROM 1 BY 1
                   UNTIL WS-I > WS-NACC OR WS-K > 0
               IF WS-ACC-ID (WS-I) = TX-ACCT
                   MOVE WS-I TO WS-K
               END-IF
           END-PERFORM
           IF WS-K = 0 AND WS-NACC < 5
               ADD 1 TO WS-NACC
               MOVE WS-NACC TO WS-K
               MOVE TX-ACCT TO WS-ACC-ID (WS-K)
               MOVE 0 TO WS-BAL (WS-K) WS-NTX (WS-K)
           END-IF.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
