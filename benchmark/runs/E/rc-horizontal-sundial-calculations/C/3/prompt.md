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
stdin = b'0\n0\n0\n'
input_files = {}
expected stdout = b'Enter latitude: Enter longitude: Enter legal meridian:  \nSine of latitude: 0.00000\nDiff longitude: 0.00000\n \nTime   Sun hour angle  Dial hour line angle\n06:00  -90.00000         0.00000\n07:00  -75.00000         0.00000\n08:00  -60.00000         0.00000\n09:00  -45.00000         0.00000\n10:00  -30.00000         0.00000\n11:00  -15.00000         0.00000\n12:00    0.00000         0.00000\n13:00   15.00000         0.00000\n14:00   30.00000         0.00000\n15:00   45.00000         0.00000\n16:00   60.00000         0.00000\n17:00   75.00000         0.00000\n18:00   90.00000         0.00000\n'
expected output_files = {}

### Example 2
stdin = b'-0.00149\n0\n0\n'
input_files = {}
expected stdout = b'Enter latitude: Enter longitude: Enter legal meridian:  \nSine of latitude: -0.00003\nDiff longitude: 0.00000\n \nTime   Sun hour angle  Dial hour line angle\n06:00  -90.00000       -90.00000\n07:00  -75.00000         0.00428\n08:00  -60.00000         0.00198\n09:00  -45.00000         0.00115\n10:00  -30.00000         0.00066\n11:00  -15.00000         0.00031\n12:00    0.00000         0.00000\n13:00   15.00000        -0.00031\n14:00   30.00000        -0.00066\n15:00   45.00000        -0.00115\n16:00   60.00000        -0.00198\n17:00   75.00000        -0.00428\n18:00   90.00000        90.00000\n'
expected output_files = {}

## COBOL program
```cobol
PROGRAM-ID. horizontal-sundial-calc.

DATA DIVISION.
WORKING-STORAGE SECTION.
01  latitude                       PIC S9(3)V9(5) COMP.
01  longitude                      PIC S9(3)V9(5) COMP.
01  legal-meridian                 PIC S9(3)V9(5) COMP.

01  lat-sine                       PIC S9(3)V9(5) COMP.
01  diff-longitude                 PIC S9(3)V9(5) COMP.

01  lat-sine-disp                  PIC -(3)9.9(5).
01  diff-longitude-disp            PIC -(3)9.9(5).

01  hour                           PIC S9 COMP.
01  sun-hour-angle                 PIC S9(3)V9(5) COMP.
01  dial-hour-line-angle           PIC S9(3)V9(5) COMP.

01  hour-disp                      PIC 99.
01  sun-hour-angle-disp            PIC -(3)9.9(5).
01  dial-hour-line-angle-disp      PIC -(3)9.9(5).

PROCEDURE DIVISION.
    DISPLAY "Enter latitude: " NO ADVANCING
    ACCEPT latitude
    DISPLAY "Enter longitude: " NO ADVANCING
    ACCEPT longitude
    DISPLAY "Enter legal meridian: " NO ADVANCING
    ACCEPT legal-meridian
    DISPLAY SPACE

    COMPUTE lat-sine, lat-sine-disp ROUNDED =
        FUNCTION SIN(latitude * 2 * FUNCTION PI / 360)
    DISPLAY "Sine of latitude: " FUNCTION TRIM(lat-sine-disp)

    SUBTRACT legal-meridian FROM longitude
        GIVING diff-longitude, diff-longitude-disp
    DISPLAY "Diff longitude: " FUNCTION TRIM(diff-longitude-disp)
    DISPLAY SPACE

    DISPLAY "Time   Sun hour angle  Dial hour line angle"
    PERFORM VARYING hour FROM -6 BY 1 UNTIL hour > 6
        COMPUTE sun-hour-angle ROUNDED = hour * 15 - diff-longitude
        COMPUTE dial-hour-line-angle ROUNDED = FUNCTION ATAN(lat-sine
            * FUNCTION TAN(sun-hour-angle * 2 * FUNCTION PI / 360))
            * 360 / (2 * FUNCTION PI)

        ADD 12 TO hour GIVING hour-disp
        MOVE sun-hour-angle TO sun-hour-angle-disp
        MOVE dial-hour-line-angle TO dial-hour-line-angle-disp
        DISPLAY hour-disp ":00 " sun-hour-angle-disp "      "
            dial-hour-line-angle-disp
    END-PERFORM
    .
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
