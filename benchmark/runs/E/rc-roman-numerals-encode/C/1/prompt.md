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
stdin = b'1\n'
input_files = {}
expected stdout = b'inp=0001 roman=I               \n'
expected output_files = {}

### Example 2
stdin = b'122\n1656\n'
input_files = {}
expected stdout = b'inp=0122 roman=CXXII           \ninp=1656 roman=MDCLVI          \n'
expected output_files = {}

## COBOL program
```cobol
IDENTIFICATION DIVISION.
PROGRAM-ID. TOROMAN.
DATA DIVISION.
working-storage section.
  01 ws-number pic 9(4) value 0.
  01 ws-save-number pic 9(4).
  01 ws-tbl-def.
    03 filler pic x(7) value '1000M  '.
    03 filler pic x(7) value '0900CM '.
    03 filler pic x(7) value '0500D  '.
    03 filler pic x(7) value '0400CD '.
    03 filler pic x(7) value '0100C  '.
    03 filler pic x(7) value '0090XC '.
    03 filler pic x(7) value '0050L  '.
    03 filler pic x(7) value '0040XL '.
    03 filler pic x(7) value '0010X  '.
    03 filler pic x(7) value '0009IX '.
    03 filler pic x(7) value '0005V  '.
    03 filler pic x(7) value '0004IV '.
    03 filler pic x(7) value '0001I  '.
  01  filler redefines ws-tbl-def.
    03 filler occurs 13 times indexed by rx.
      05 ws-tbl-divisor    pic 9(4).
      05 ws-tbl-roman-ch   pic x(1) occurs 3 times indexed by cx.
  01 ocx pic 99.
  01 ws-roman.
    03 ws-roman-ch         pic x(1) occurs 16 times.
PROCEDURE DIVISION.
  accept ws-number
  perform
  until ws-number = 0
    move ws-number to ws-save-number
    if ws-number > 0 and ws-number < 4000
      initialize ws-roman
      move 0 to ocx
      perform varying rx from 1 by +1
      until ws-number = 0
        perform until ws-number < ws-tbl-divisor (rx)
          perform varying cx from 1 by +1
  		  until ws-tbl-roman-ch (rx, cx) = spaces
            compute ocx = ocx + 1
            move ws-tbl-roman-ch (rx, cx) to ws-roman-ch (ocx)
          end-perform
          compute ws-number = ws-number - ws-tbl-divisor (rx)
        end-perform
      end-perform
      display 'inp=' ws-save-number ' roman=' ws-roman
    else
      display 'inp=' ws-save-number ' invalid'
    end-if
    accept ws-number
  end-perform
  .
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
