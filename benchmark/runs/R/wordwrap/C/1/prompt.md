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
input_files = {'TEXT.DAT': b'03\n'}
expected stdout = b'BAD WIDTH 03\nLINES 000\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'TEXT.DAT': b'27\n'}
expected stdout = b'WIDTH 27\nLINES 000\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. WORDWRAP.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TEXT-FILE ASSIGN TO "TEXT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD TEXT-FILE.
       01 TEXT-REC.
          05 TX-WIDTH       PIC 99.
          05 TX-TEXT        PIC X(60).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-PTR            PIC 99.
       01 WS-WORD           PIC X(60).
       01 WS-WLEN           PIC 99.
       01 WS-LINE           PIC X(40).
       01 WS-LPTR           PIC 99.
       01 WS-USED           PIC 99.
       01 WS-START          PIC 99.
       01 WS-PART           PIC 99.
       01 WS-LINES          PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT TEXT-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ TEXT-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM WRAP-TEXT
               END-READ
           END-PERFORM
           CLOSE TEXT-FILE
           DISPLAY "LINES " WS-LINES
           STOP RUN.

       WRAP-TEXT.
           IF TX-WIDTH < 5 OR TX-WIDTH > 40
               DISPLAY "BAD WIDTH " TX-WIDTH
           ELSE
               DISPLAY "WIDTH " TX-WIDTH
               MOVE SPACES TO WS-LINE
               MOVE 0 TO WS-USED
               MOVE 1 TO WS-PTR
               PERFORM UNTIL WS-PTR > 60
                   MOVE SPACES TO WS-WORD
                   MOVE 0 TO WS-WLEN
                   UNSTRING TX-TEXT DELIMITED BY ALL SPACE
                       INTO WS-WORD COUNT IN WS-WLEN
                       WITH POINTER WS-PTR
                   END-UNSTRING
                   IF WS-WLEN > 0
                       PERFORM PLACE-WORD
                   END-IF
               END-PERFORM
               IF WS-USED > 0
                   PERFORM FLUSH-LINE
               END-IF
           END-IF.

       PLACE-WORD.
           MOVE 1 TO WS-START
           PERFORM UNTIL WS-WLEN - WS-START < TX-WIDTH
               IF WS-USED > 0
                   PERFORM FLUSH-LINE
               END-IF
               MOVE WS-WORD (WS-START:TX-WIDTH - 1) TO WS-LINE
               MOVE "-" TO WS-LINE (TX-WIDTH:1)
               MOVE TX-WIDTH TO WS-USED
               PERFORM FLUSH-LINE
               COMPUTE WS-START = WS-START + TX-WIDTH - 1
           END-PERFORM
           COMPUTE WS-PART = WS-WLEN - WS-START + 1
           IF WS-USED > 0 AND WS-USED + 1 + WS-PART > TX-WIDTH
               PERFORM FLUSH-LINE
           END-IF
           IF WS-USED = 0
               MOVE 1 TO WS-LPTR
           ELSE
               COMPUTE WS-LPTR = WS-USED + 2
           END-IF
           STRING WS-WORD (WS-START:WS-PART) DELIMITED BY SIZE
               INTO WS-LINE WITH POINTER WS-LPTR
           COMPUTE WS-USED = WS-LPTR - 1.

       FLUSH-LINE.
           ADD 1 TO WS-LINES
           DISPLAY "|" WS-LINE (1:TX-WIDTH) "|"
           MOVE SPACES TO WS-LINE
           MOVE 0 TO WS-USED.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
