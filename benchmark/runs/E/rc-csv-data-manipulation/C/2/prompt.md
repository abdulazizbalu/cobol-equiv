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
input_files = {'csv.txt': b'0,0,0,0,0\n'}
expected stdout = b''
expected output_files = {'new.csv.txt': b'0,0,0,0,0,SUM\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n'}

### Example 2
stdin = b''
input_files = {'csv.txt': b'150,752,16161,1,99998\n'}
expected stdout = b''
expected output_files = {'new.csv.txt': b'150,752,16161,1,99998,SUM\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n'}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CSV.
       AUTHOR.  Bill Gunshannon.
       INSTALLATION.  Home.
       DATE-WRITTEN.  19 December 2021.

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
           REPOSITORY.
           FUNCTION ALL INTRINSIC.

       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
            SELECT CSV-File ASSIGN TO "csv.txt"
                 ORGANIZATION IS LINE SEQUENTIAL.
            SELECT Out-File ASSIGN TO "new.csv.txt"
                 ORGANIZATION IS LINE SEQUENTIAL.


       DATA DIVISION.

       FILE SECTION.

       FD  CSV-File
           DATA RECORD IS CSV-Record.
       01  CSV-Record.
           05 Field1                  PIC X(64).

       FD  Out-File
           DATA RECORD IS Out-Line.
       01  Out-Line   PIC X(80).

       WORKING-STORAGE SECTION.

       01 Eof                   PIC X     VALUE 'F'.

       01  CSV-Data.
           05  CSV-Col1             PIC 9(5).
           05  CSV-Col2             PIC 9(5).
           05  CSV-Col3             PIC 9(5).
           05  CSV-Col4             PIC 9(5).
           05  CSV-Col5             PIC 9(5).

        01  CSV-Sum                  PIC ZZZ9.
        01  CSV-Sum-Alpha
                REDEFINES     CSV-Sum  PIC X(4).

       PROCEDURE DIVISION.

       Main-Program.
           OPEN INPUT  CSV-File
           OPEN OUTPUT Out-File
           PERFORM Read-a-Record
           PERFORM Build-Header
           PERFORM UNTIL Eof = 'T'
              PERFORM Read-a-Record
              IF Eof NOT EQUAL 'T' PERFORM Process-a-Record
           END-PERFORM
           CLOSE CSV-File
           CLOSE Out-File
           STOP RUN.

       Read-a-Record.
           READ CSV-File
              AT END MOVE 'T' TO Eof
           END-READ.

        Build-Header.
            STRING TRIM(CSV-Record), ",SUM" INTO Out-Line.
            WRITE Out-Line.
            MOVE SPACES TO Out-Line.

        Process-a-Record.
            UNSTRING CSV-Record DELIMITED BY ',' INTO
                  CSV-Col1 CSV-Col2 CSV-Col3 CSV-Col4 CSV-Col5.
            COMPUTE CSV-Sum =
                  CSV-Col1 + CSV-Col2 + CSV-Col3 + CSV-Col4 + CSV-Col5.
            STRING TRIM(CSV-Record), "," TRIM(CSV-Sum-Alpha)
                   INTO Out-Line.
            WRITE Out-Line.
            MOVE SPACES TO Out-Line.

       END-PROGRAM.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
