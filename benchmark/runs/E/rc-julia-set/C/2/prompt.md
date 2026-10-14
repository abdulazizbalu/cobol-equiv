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
stdin = b'\n\n'
input_files = {}
expected stdout = b'                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n                          #####                          \n                   ###################                   \n                #########################                \n              #############################              \n            #################################            \n           ###################################           \n          #####################################          \n         #######################################         \n         #######################################         \n        ########################################         \n        ########################################         \n         #######################################         \n         #######################################         \n         ######################################          \n          #####################################          \n           ###################################           \n             ###############################             \n              ############################               \n                 #######################                 \n                    #################                    \n                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n'
expected output_files = {}

### Example 2
stdin = b'P\n\n'
input_files = {}
expected stdout = b'                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n                          #####                          \n                   ###################                   \n                #########################                \n              #############################              \n            #################################            \n           ###################################           \n          #####################################          \n         #######################################         \n         #######################################         \n        ########################################         \n        ########################################         \n         #######################################         \n         #######################################         \n         ######################################          \n          #####################################          \n           ###################################           \n             ###############################             \n              ############################               \n                 #######################                 \n                    #################                    \n                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n                                                         \n'
expected output_files = {}

## COBOL program
```cobol
IDENTIFICATION DIVISION.
PROGRAM-ID. JULIA-SET-PROGRAM.
DATA DIVISION.
WORKING-STORAGE SECTION.
01  WS-COMPLEX-CONSTANT.
    05 C-REAL             PIC S9V999.
    05 C-IMAGINARY        PIC S9V999.
01  WS-ARGAND-PLANE.
    05 X                  PIC S9(9)V999.
    05 Y                  PIC S9(9)V999.
01  WS-COMPLEX-VARIABLE.
    05 Z-REAL             PIC S9(9)V999.
    05 Z-IMAGINARY        PIC S9(9)V999.
01  WS-TEMPORARY-RESULTS.
    05 X-SQUARED          PIC S9(9)V999.
    05 Y-SQUARED          PIC S9(9)V999.
    05 X-TIMES-Y          PIC S9(9)V999.
    05 Z-REAL-SQUARED     PIC S9(9)V999.
01  WS-LOOP-COUNTERS.
    05 HORIZONTAL         PIC 999.
    05 VERTICAL           PIC 999.
    05 ITERATIONS         PIC 99.
77  WS-PLOT-CHARACTER     PIC X.
PROCEDURE DIVISION.
INPUT-COMPLEX-CONSTANT-PARAGRAPH.
    ACCEPT C-REAL      FROM CONSOLE.
    ACCEPT C-IMAGINARY FROM CONSOLE.
CONTROL-PARAGRAPH.
    PERFORM OUTER-LOOP-PARAGRAPH  VARYING VERTICAL   FROM 1 BY 10
    UNTIL VERTICAL IS GREATER THAN 320.
    STOP RUN.
OUTER-LOOP-PARAGRAPH.
    PERFORM COMPUTATION-PARAGRAPH VARYING HORIZONTAL FROM 1 BY 10
    UNTIL HORIZONTAL IS GREATER THAN 560.
    DISPLAY '' UPON CONSOLE.
COMPUTATION-PARAGRAPH.
    SUBTRACT 280   FROM HORIZONTAL GIVING X.
    SUBTRACT 160   FROM VERTICAL   GIVING Y.
    DIVIDE   X     BY   200        GIVING X.
    DIVIDE   Y     BY   100        GIVING Y.
    MOVE     '#'   TO   WS-PLOT-CHARACTER.
    PERFORM COMPLEX-MULTIPLICATION-PARAGRAPH
    VARYING ITERATIONS FROM   1  BY      1
    UNTIL   ITERATIONS        IS GREATER THAN 50
    OR      WS-PLOT-CHARACTER IS EQUAL   TO   SPACE.
    DISPLAY WS-PLOT-CHARACTER UPON CONSOLE WITH NO ADVANCING.
COMPLEX-MULTIPLICATION-PARAGRAPH.
    MULTIPLY X         BY   X         GIVING X-SQUARED.
    MULTIPLY Y         BY   Y         GIVING Y-SQUARED.
    SUBTRACT Y-SQUARED FROM X-SQUARED GIVING Z-REAL.
    ADD      C-REAL    TO   Z-REAL.
    MULTIPLY X         BY   Y         GIVING X-TIMES-Y.
    MULTIPLY X-TIMES-Y BY   2         GIVING Z-IMAGINARY.
    ADD C-IMAGINARY    TO   Z-IMAGINARY.
    MULTIPLY Z-REAL    BY   Z-REAL    GIVING Z-REAL-SQUARED.
    IF  Z-REAL-SQUARED IS   GREATER   THAN   10000 THEN
    MOVE SPACE         TO   WS-PLOT-CHARACTER.
    MOVE Z-REAL        TO   X.
    MOVE Z-IMAGINARY   TO   Y.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
