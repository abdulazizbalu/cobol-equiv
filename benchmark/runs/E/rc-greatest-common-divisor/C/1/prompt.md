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
stdin = b'0\n0\n'
input_files = {}
expected stdout = b'Enter first number, max 10 digits.\nEnter second number, max 10 digits.\nThe gcd is 0000000000\n'
expected output_files = {}

### Example 2
stdin = b'1690\n0\n'
input_files = {}
expected stdout = b'Enter first number, max 10 digits.\nEnter second number, max 10 digits.\nThe gcd is 0000001690\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. GCD.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 A        PIC 9(10)   VALUE ZEROES.
       01 B        PIC 9(10)   VALUE ZEROES.
       01 TEMP     PIC 9(10)   VALUE ZEROES.

       PROCEDURE DIVISION.
       Begin.
           DISPLAY "Enter first number, max 10 digits."
           ACCEPT A
           DISPLAY "Enter second number, max 10 digits."
           ACCEPT B
           IF A < B
             MOVE B TO TEMP
             MOVE A TO B
             MOVE TEMP TO B
           END-IF

           PERFORM UNTIL B = 0
             MOVE A TO TEMP
             MOVE B TO A
             DIVIDE TEMP BY B GIVING TEMP REMAINDER B
           END-PERFORM
           DISPLAY "The gcd is " A
           STOP RUN.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
