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
input_files = {'ACCTREC': b'        \x00\x00\x00\x00\x0c\x00\x00\x00\x00\x0c                                                                                                                                                        '}
expected stdout = b'Not Found\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'ACCTREC': b"s`o' S_^\x00\x00\x00\x00\x0c\x00\x00\x00\x00\x0c                                                                                                                                                        "}
expected stdout = b'Not Found\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    SRCHBIN.
       AUTHOR.        Otto B. Boolean.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ACCT-REC   ASSIGN TO ACCTREC.
       DATA DIVISION.
       FILE SECTION.
       FD  ACCT-REC RECORDING MODE F.
       01  ACCT-FIELDS        PIC X(170).
       WORKING-STORAGE SECTION.
       01  FLAGS.
           05  LASTREC            PIC X VALUE SPACE.
               88  END-OF-FILE          VALUE 'Y'.
           05  TABLE-VAR          PIC S9(4) COMP.
           05  TABLE-MAX          PIC S9(4) COMP VALUE 45.
       01  ACCT-TABLE.
           05  ACCT-TABLE-ITEM OCCURS 45 TIMES ASCENDING KEY IS ACCT-NO
               INDEXED BY TABLE-IDX.
               10  ACCT-NO            PIC X(8).
               10  ACCT-LIMIT         PIC S9(7)V99 COMP-3.
               10  ACCT-BALANCE       PIC S9(7)V99 COMP-3.
               10  LAST-NAME          PIC X(20).
               10  FIRST-NAME         PIC X(15).
               10  CLIENT-ADDR.
                   15  STREET-ADDR    PIC X(25).
                   15  CITY-COUNTY    PIC X(20).
                   15  USA-STATE      PIC X(15).
               10  RESERVED           PIC X(7).
               10  COMMENTS           PIC X(50).
       PROCEDURE DIVISION.
       OPEN-FILES.
           OPEN INPUT ACCT-REC.
       LOAD-TABLES.
           PERFORM READ-RECORD.
           PERFORM VARYING TABLE-VAR FROM 1 BY 1
             UNTIL TABLE-VAR = TABLE-MAX OR END-OF-FILE
               MOVE ACCT-FIELDS TO ACCT-TABLE-ITEM (TABLE-VAR)
               PERFORM READ-RECORD
           END-PERFORM.
       SEARCH-RECORD.
           SET TABLE-IDX TO 1.
           SEARCH ALL ACCT-TABLE-ITEM
               AT END DISPLAY "Not Found"
               WHEN ACCT-NO (TABLE-IDX) = 18011809
                   DISPLAY "User with Acct No 18011809 is found!".
       CLOSE-STOP.
           CLOSE ACCT-REC.
           GOBACK.
       READ-RECORD.
           READ ACCT-REC
               AT END SET END-OF-FILE TO TRUE
           END-READ.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
