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
stdin = b'1601\n'
input_files = {}
expected stdout = b'Enter calendar year (1601 thru 9999): Year 1601 is NOT a leap year\n'
expected output_files = {}

### Example 2
stdin = b'1602\n'
input_files = {}
expected stdout = b'Enter calendar year (1601 thru 9999): Year 1602 is NOT a leap year\n'
expected output_files = {}

## COBOL program
```cobol
       program-id. leap-yr.
       data division.
       working-storage section.
       1 input-year pic 9999.
       1 binary.
        2 int-date pic 9(8).
        2 cal-mo-day pic 9(4).
       procedure division.
           display "Enter calendar year (1601 thru 9999): "
               with no advancing
           accept input-year
           if input-year >= 1601 and <= 9999
           then
               compute int-date = function integer-of-day
                   ( input-year * 1000 + 60 )
               compute cal-mo-day = function mod (
                   (function date-of-integer ( int-date )) 10000 )
               display "Year " input-year space with no advancing
               if cal-mo-day = 229
                   display "is a leap year"
               else
                   display "is NOT a leap year"
               end-if
           else
               display "Input date is not within range"
           end-if
           stop run
           .
       end program leap-yr.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
