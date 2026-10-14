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
stdin = b'0\n'
input_files = {}
expected stdout = b'What place of the Fibonacci Sequence would you like (<173)? '
expected output_files = {}

### Example 2
stdin = b'34\n'
input_files = {}
expected stdout = b'What place of the Fibonacci Sequence would you like (<173)? 0                                   \n1                                   \n2                                   \n3                                   \n5                                   \n8                                   \n13                                  \n21                                  \n34                                  \n55                                  \n89                                  \n144                                 \n233                                 \n377                                 \n610                                 \n987                                 \n1597                                \n2584                                \n4181                                \n6765                                \n10946                               \n17711                               \n28657                               \n46368                               \n75025                               \n121393                              \n196418                              \n317811                              \n514229                              \n832040                              \n1346269                             \n2178309                             \n3524578                             \n5702887                             \n'
expected output_files = {}

## COBOL program
```cobol
Program-ID. Fibonacci-Sequence.
Data Division.
Working-Storage Section.
  01  FIBONACCI-PROCESSING.
    05  FIBONACCI-NUMBER  PIC 9(36)   VALUE 0.
    05  FIB-ONE           PIC 9(36)   VALUE 0.
    05  FIB-TWO           PIC 9(36)   VALUE 1.
  01  DESIRED-COUNT       PIC 9(4).
  01  FORMATTING.
    05  INTERM-RESULT     PIC Z(35)9.
    05  FORMATTED-RESULT  PIC X(36).
    05  FORMATTED-SPACE   PIC x(35).
Procedure Division.
  000-START-PROGRAM.
    Display "What place of the Fibonacci Sequence would you like (<173)? " with no advancing.
    Accept DESIRED-COUNT.
    If DESIRED-COUNT is less than 1
      Stop run.
    If DESIRED-COUNT is less than 2
      Move FIBONACCI-NUMBER to INTERM-RESULT
      Move INTERM-RESULT to FORMATTED-RESULT
      Unstring FORMATTED-RESULT delimited by all spaces into FORMATTED-SPACE,FORMATTED-RESULT
      Display FORMATTED-RESULT
      Stop run.
    Subtract 1 from DESIRED-COUNT.
    Move FIBONACCI-NUMBER to INTERM-RESULT.
    Move INTERM-RESULT to FORMATTED-RESULT.
    Unstring FORMATTED-RESULT delimited by all spaces into FORMATTED-SPACE,FORMATTED-RESULT.
    Display FORMATTED-RESULT.
    Perform 100-COMPUTE-FIBONACCI until DESIRED-COUNT = zero.
    Stop run.
  100-COMPUTE-FIBONACCI.
    Compute FIBONACCI-NUMBER = FIB-ONE + FIB-TWO.
    Move FIB-TWO to FIB-ONE.
    Move FIBONACCI-NUMBER to FIB-TWO.
    Subtract 1 from DESIRED-COUNT.
    Move FIBONACCI-NUMBER to INTERM-RESULT.
    Move INTERM-RESULT to FORMATTED-RESULT.
    Unstring FORMATTED-RESULT delimited by all spaces into FORMATTED-SPACE,FORMATTED-RESULT.
    Display FORMATTED-RESULT.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
