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
stdin = b'\n'
input_files = {}
expected stdout = b'                                                                                \n'
expected output_files = {}

### Example 2
stdin = b'J=e^\nFALSE\ny606"\n'
input_files = {}
expected stdout = b'J=e^                                                                            \nFALSE                                                                           \ny606"                                                                           \n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. input-loop.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT in-stream ASSIGN TO KEYBOARD
               ORGANIZATION LINE SEQUENTIAL
               FILE STATUS in-stream-status.

       DATA DIVISION.
       FILE SECTION.
       FD  in-stream.
       01  stream-line                 PIC X(80).

       WORKING-STORAGE SECTION.
       01  in-stream-status            PIC 99.
           88  end-of-stream           VALUE 10.

       PROCEDURE DIVISION.
           OPEN INPUT in-stream

           PERFORM UNTIL EXIT
               READ in-stream
                   AT END
                       EXIT PERFORM
               END-READ
               DISPLAY stream-line
           END-PERFORM

           CLOSE in-stream
           .
       END PROGRAM input-loop.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
