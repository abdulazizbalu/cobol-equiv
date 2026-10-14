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
input_files = {'File.txt': b'\n'}
expected stdout = b'Letter Frequency Distribution\n-----------------------------\nA :     0          N :     0\nB :     0          O :     0\nC :     0          P :     0\nD :     0          Q :     0\nE :     0          R :     0\nF :     0          S :     0\nG :     0          T :     0\nH :     0          U :     0\nI :     0          V :     0\nJ :     0          W :     0\nK :     0          X :     0\nL :     0          Y :     0\nM :     0          Z :     0\n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'File.txt': b'None\n'}
expected stdout = b'Letter Frequency Distribution\n-----------------------------\nA :     0          N :     4\nB :     0          O :     2\nC :     0          P :     0\nD :     0          Q :     0\nE :     2          R :     0\nF :     0          S :     0\nG :     0          T :     0\nH :     0          U :     0\nI :     0          V :     0\nJ :     0          W :     0\nK :     0          X :     0\nL :     0          Y :     0\nM :     0          Z :     0\n'
expected output_files = {}

## COBOL program
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. Letter-Frequency.
       AUTHOR.  Bill Gunshannon.
       INSTALLATION.  Home.
       DATE-WRITTEN.  12 December 2021.

       ENVIRONMENT DIVISION.

       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
            SELECT Text-File ASSIGN TO "File.txt"
                 ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.

       FILE SECTION.

       FD  Text-File
           DATA RECORD IS Record-Name.
       01  Record-Name           PIC X(80).


       WORKING-STORAGE SECTION.

       01 Eof                   PIC X     VALUE 'F'.

       01  Letter-cnt.
           05  A-cnt            PIC 9(5)    VALUE 0.
           05  B-cnt            PIC 9(5)    VALUE 0.
           05  C-cnt            PIC 9(5)    VALUE 0.
           05  D-cnt            PIC 9(5)    VALUE 0.
           05  E-cnt            PIC 9(5)    VALUE 0.
           05  F-cnt            PIC 9(5)    VALUE 0.
           05  G-cnt            PIC 9(5)    VALUE 0.
           05  H-cnt            PIC 9(5)    VALUE 0.
           05  I-cnt            PIC 9(5)    VALUE 0.
           05  J-cnt            PIC 9(5)    VALUE 0.
           05  K-cnt            PIC 9(5)    VALUE 0.
           05  L-cnt            PIC 9(5)    VALUE 0.
           05  M-cnt            PIC 9(5)    VALUE 0.
           05  N-cnt            PIC 9(5)    VALUE 0.
           05  O-cnt            PIC 9(5)    VALUE 0.
           05  P-cnt            PIC 9(5)    VALUE 0.
           05  Q-cnt            PIC 9(5)    VALUE 0.
           05  R-cnt            PIC 9(5)    VALUE 0.
           05  S-cnt            PIC 9(5)    VALUE 0.
           05  T-cnt            PIC 9(5)    VALUE 0.
           05  U-cnt            PIC 9(5)    VALUE 0.
           05  V-cnt            PIC 9(5)    VALUE 0.
           05  W-cnt            PIC 9(5)    VALUE 0.
           05  X-cnt            PIC 9(5)    VALUE 0.
           05  Y-cnt            PIC 9(5)    VALUE 0.
           05  Z-cnt            PIC 9(5)    VALUE 0.

       01  Letter-disp.
           05  A-cnt            PIC ZZZZ9.
           05  B-cnt            PIC ZZZZ9.
           05  C-cnt            PIC ZZZZ9.
           05  D-cnt            PIC ZZZZ9.
           05  E-cnt            PIC ZZZZ9.
           05  F-cnt            PIC ZZZZ9.
           05  G-cnt            PIC ZZZZ9.
           05  H-cnt            PIC ZZZZ9.
           05  I-cnt            PIC ZZZZ9.
           05  J-cnt            PIC ZZZZ9.
           05  K-cnt            PIC ZZZZ9.
           05  L-cnt            PIC ZZZZ9.
           05  M-cnt            PIC ZZZZ9.
           05  N-cnt            PIC ZZZZ9.
           05  O-cnt            PIC ZZZZ9.
           05  P-cnt            PIC ZZZZ9.
           05  Q-cnt            PIC ZZZZ9.
           05  R-cnt            PIC ZZZZ9.
           05  S-cnt            PIC ZZZZ9.
           05  T-cnt            PIC ZZZZ9.
           05  U-cnt            PIC ZZZZ9.
           05  V-cnt            PIC ZZZZ9.
           05  W-cnt            PIC ZZZZ9.
           05  X-cnt            PIC ZZZZ9.
           05  Y-cnt            PIC ZZZZ9.
           05  Z-cnt            PIC ZZZZ9.

       PROCEDURE DIVISION.

       Main-Program.
           OPEN INPUT  Text-File
           PERFORM UNTIL Eof = 'T'
              READ  Text-File
                    AT END MOVE 'T' to Eof
              END-READ
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING A-cnt OF Letter-cnt  FOR ALL 'A'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING B-cnt OF Letter-cnt  FOR ALL 'B'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING C-cnt OF Letter-cnt  FOR ALL 'C'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING D-cnt OF Letter-cnt  FOR ALL 'D'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING E-cnt OF Letter-cnt  FOR ALL 'E'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING F-cnt OF Letter-cnt  FOR ALL 'F'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING G-cnt OF Letter-cnt  FOR ALL 'G'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING H-cnt OF Letter-cnt  FOR ALL 'H'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING I-cnt OF Letter-cnt  FOR ALL 'I'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING J-cnt OF Letter-cnt  FOR ALL 'J'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING K-cnt OF Letter-cnt  FOR ALL 'K'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING L-cnt OF Letter-cnt  FOR ALL 'L'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING M-cnt OF Letter-cnt  FOR ALL 'M'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING N-cnt OF Letter-cnt  FOR ALL 'N'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING O-cnt OF Letter-cnt  FOR ALL 'O'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING P-cnt OF Letter-cnt  FOR ALL 'P'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING Q-cnt OF Letter-cnt  FOR ALL 'Q'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING R-cnt OF Letter-cnt  FOR ALL 'R'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING S-cnt OF Letter-cnt  FOR ALL 'S'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING T-cnt OF Letter-cnt  FOR ALL 'T'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING U-cnt OF Letter-cnt  FOR ALL 'U'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING V-cnt OF Letter-cnt  FOR ALL 'V'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING W-cnt OF Letter-cnt  FOR ALL 'W'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING X-cnt OF Letter-cnt  FOR ALL 'X'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING Y-cnt OF Letter-cnt  FOR ALL 'Y'
           INSPECT FUNCTION UPPER-CASE(Record-Name)
                   TALLYING Z-cnt OF Letter-cnt  FOR ALL 'Z'
           END-PERFORM.
           CLOSE Text-File.
           MOVE CORRESPONDING Letter-cnt To Letter-disp.
           DISPLAY 'Letter Frequency Distribution'.
           DISPLAY '-----------------------------'.
           DISPLAY 'A : ' A-cnt OF Letter-disp '          '
                   'N : ' N-cnt OF Letter-disp.
           DISPLAY 'B : ' B-cnt OF Letter-disp '          '
                   'O : ' O-cnt OF Letter-disp.
           DISPLAY 'C : ' C-cnt OF Letter-disp '          '
                   'P : ' P-cnt OF Letter-disp.
           DISPLAY 'D : ' D-cnt OF Letter-disp '          '
                   'Q : ' Q-cnt OF Letter-disp.
           DISPLAY 'E : ' E-cnt OF Letter-disp '          '
                   'R : ' R-cnt OF Letter-disp.
           DISPLAY 'F : ' F-cnt OF Letter-disp '          '
                   'S : ' S-cnt OF Letter-disp.
           DISPLAY 'G : ' G-cnt OF Letter-disp '          '
                   'T : ' T-cnt OF Letter-disp.
           DISPLAY 'H : ' H-cnt OF Letter-disp '          '
                   'U : ' U-cnt OF Letter-disp.
           DISPLAY 'I : ' I-cnt OF Letter-disp '          '
                   'V : ' V-cnt OF Letter-disp.
           DISPLAY 'J : ' J-cnt OF Letter-disp '          '
                   'W : ' W-cnt OF Letter-disp.
           DISPLAY 'K : ' K-cnt OF Letter-disp '          '
                   'X : ' X-cnt OF Letter-disp.
           DISPLAY 'L : ' L-cnt OF Letter-disp '          '
                   'Y : ' Y-cnt OF Letter-disp.
           DISPLAY 'M : ' M-cnt OF Letter-disp '          '
                   'Z : ' Z-cnt OF Letter-disp.
           STOP RUN.


       END-PROGRAM.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
