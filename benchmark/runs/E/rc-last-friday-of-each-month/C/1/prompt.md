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
expected stdout = b'Enter a calendar year (1601 thru 9999): 1601-01-26\n1601-02-23\n1601-03-30\n1601-04-27\n1601-05-25\n1601-06-29\n1601-07-27\n1601-08-31\n1601-09-28\n1601-10-26\n1601-11-30\n1601-12-28\n'
expected output_files = {}

### Example 2
stdin = b'3931\n'
input_files = {}
expected stdout = b'Enter a calendar year (1601 thru 9999): 3931-01-30\n3931-02-27\n3931-03-27\n3931-04-24\n3931-05-29\n3931-06-26\n3931-07-31\n3931-08-28\n3931-09-25\n3931-10-30\n3931-11-27\n3931-12-25\n'
expected output_files = {}

## COBOL program
```cobol
       program-id. last-fri.
       data division.
       working-storage section.
       1 wk-date.
        2 yr pic 9999.
        2 mo pic 99 value 1.
        2 da pic 99 value 1.
       1 rd-date redefines wk-date pic 9(8).
       1 binary.
        2 int-date pic 9(8).
        2 dow pic 9(4).
        2 friday pic 9(4) value 5.
       procedure division.
           display "Enter a calendar year (1601 thru 9999): "
               with no advancing
           accept yr
           if yr >= 1601 and <= 9999
               continue
           else
               display "Invalid year"
               stop run
           end-if
           perform 12 times
               move 1 to da
               add 1 to mo
               if mo > 12
                   move 12 to mo
                   move 31 to da
               end-if
               compute int-date = function
                   integer-of-date (rd-date)
               if mo =12 and da = 31
                   continue
               else
                   subtract 1 from int-date
               end-if
               compute rd-date = function
                   date-of-integer (int-date)
               compute dow = function mod
                   ((int-date - 1) 7) + 1
               compute dow = function mod ((dow - friday) 7)
               subtract dow from da
               display yr "-" mo "-" da
               add 1 to mo
           end-perform
           stop run
           .
       end program last-fri.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
