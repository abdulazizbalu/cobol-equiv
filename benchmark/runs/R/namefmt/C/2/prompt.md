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
input_files = {'NAMES.DAT': b',\n'}
expected stdout = b'NO SPLIT ,\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'NAMES.DAT': b':JY-"c*5?,)Tq?T\nJ\'<u9%bAl7}\ng=\n'}
expected stdout = b'[)Tq?T :JY-"c*5?] 02\nNO SPLIT J\'<u9%bAl7}\nNO SPLIT g=\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. NAMEFMT.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT NAME-FILE ASSIGN TO "NAMES.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD NAME-FILE.
       01 NAME-REC          PIC X(30).
       WORKING-STORAGE SECTION.
       01 WS-EOF            PIC X VALUE "N".
       01 WS-TEXT           PIC X(30).
       01 WS-LEN            PIC 99.
       01 WS-COMMA          PIC 99.
       01 WS-S              PIC 99.
       01 WS-I              PIC 99.
       01 WS-P              PIC 99.
       01 WS-N              PIC 99.
       01 WS-WORDS          PIC 99.
       01 WS-OUT            PIC X(40).
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT NAME-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ NAME-FILE INTO WS-TEXT
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM FORMAT-NAME
               END-READ
           END-PERFORM
           CLOSE NAME-FILE
           STOP RUN.

       FORMAT-NAME.
           MOVE 30 TO WS-LEN
           PERFORM UNTIL WS-LEN = 0
                   OR WS-TEXT (WS-LEN:1) NOT = SPACE
               SUBTRACT 1 FROM WS-LEN
           END-PERFORM
           IF WS-LEN = 0
               DISPLAY "EMPTY"
           ELSE
               MOVE 0 TO WS-COMMA
               PERFORM VARYING WS-I FROM 1 BY 1
                       UNTIL WS-I > WS-LEN OR WS-COMMA > 0
                   IF WS-TEXT (WS-I:1) = ","
                       MOVE WS-I TO WS-COMMA
                   END-IF
               END-PERFORM
               IF WS-COMMA < 2 OR WS-COMMA = WS-LEN
                   DISPLAY "NO SPLIT " WS-TEXT (1:WS-LEN)
               ELSE
                   COMPUTE WS-S = WS-COMMA + 1
                   PERFORM UNTIL WS-S > WS-LEN
                           OR WS-TEXT (WS-S:1) NOT = SPACE
                       ADD 1 TO WS-S
                   END-PERFORM
                   IF WS-S > WS-LEN
                       DISPLAY "NO SPLIT " WS-TEXT (1:WS-LEN)
                   ELSE
                       PERFORM BUILD-OUTPUT
                   END-IF
               END-IF
           END-IF.

       BUILD-OUTPUT.
           MOVE SPACES TO WS-OUT
           COMPUTE WS-N = WS-LEN - WS-S + 1
           MOVE WS-TEXT (WS-S:WS-N) TO WS-OUT (1:WS-N)
           INSPECT WS-OUT (1:1) CONVERTING
               "abcdefghijklmnopqrstuvwxyz" TO
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
           COMPUTE WS-P = WS-N + 2
           COMPUTE WS-N = WS-COMMA - 1
           MOVE WS-TEXT (1:WS-N) TO WS-OUT (WS-P:WS-N)
           ADD WS-N TO WS-P
           SUBTRACT 1 FROM WS-P
           MOVE 1 TO WS-WORDS
           PERFORM VARYING WS-I FROM 2 BY 1 UNTIL WS-I > WS-P
               IF WS-OUT (WS-I:1) NOT = SPACE
                       AND WS-OUT (WS-I - 1:1) = SPACE
                   ADD 1 TO WS-WORDS
               END-IF
           END-PERFORM
           DISPLAY "[" WS-OUT (1:WS-P) "] " WS-WORDS.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
