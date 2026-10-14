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
input_files = {'unixdict.txt': b'a\n'}
expected stdout = b''
expected output_files = {}

### Example 2
stdin = b''
input_files = {'unixdict.txt': b'nj\n'}
expected stdout = b''
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ABC-WORDS.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT DICT ASSIGN TO DISK
           ORGANIZATION LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD DICT
           LABEL RECORD STANDARD
           VALUE OF FILE-ID IS "unixdict.txt".
       01 WORD            PIC X(32).

       WORKING-STORAGE SECTION.
       01 A               PIC 99.
       01 B               PIC 99.
       01 C               PIC 99.
       01 X               PIC 99.

       PROCEDURE DIVISION.
       BEGIN.
           OPEN INPUT DICT.

       READ-WORD.
           READ DICT, AT END CLOSE DICT, STOP RUN.
           PERFORM CHECK-WORD.
           GO TO READ-WORD.

       CHECK-WORD.
           MOVE ZERO TO A, B, C, X.
           INSPECT WORD TALLYING A FOR CHARACTERS BEFORE INITIAL 'a'.
           INSPECT WORD TALLYING B FOR CHARACTERS BEFORE INITIAL 'b'.
           INSPECT WORD TALLYING C FOR CHARACTERS BEFORE INITIAL 'c'.
           INSPECT WORD TALLYING X FOR CHARACTERS BEFORE INITIAL ' '.
           IF A IS LESS THAN B
           AND B IS LESS THAN C
           AND C IS LESS THAN X,
               DISPLAY WORD.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
