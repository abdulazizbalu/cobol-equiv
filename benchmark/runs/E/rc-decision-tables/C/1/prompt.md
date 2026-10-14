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
stdin = b'Y\nY\nY\n'
input_files = {}
expected stdout = b' \nThe printer does not print (Y or N) A red light is flashing (Y or N) The printer is unrecognized (Y or N)  \nCheck the printer-computer cable\nEnsure printer software is installed\nCheck/replace ink\n \n'
expected output_files = {}

### Example 2
stdin = b'N\nY\nY\n'
input_files = {}
expected stdout = b' \nThe printer does not print (Y or N) A red light is flashing (Y or N) The printer is unrecognized (Y or N)  \nEnsure printer software is installed\nCheck/replace ink\n \n'
expected output_files = {}

## COBOL program
```cobol
        >> SOURCE FORMAT FREE
identification division.
program-id. 'decisiontable'.

environment division.
configuration section.
repository.
    function all intrinsic.

data division.

working-storage section.

01  conditions.
    03  notprinting pic x.
    03  flashing pic x.
    03  notrecognized pic x.

procedure division.
start-decision-table.

display space

display 'The printer does not print (Y or N) ' with no advancing
accept notprinting

display 'A red light is flashing (Y or N) ' with no advancing
accept flashing

display 'The printer is unrecognized (Y or N) ' with no advancing
accept notrecognized

move upper-case(conditions) to conditions

display space




evaluate notprinting also flashing also notrecognized

when 'Y' also 'Y' also 'Y'
    display 'Check the printer-computer cable'
    display 'Ensure printer software is installed'
    display 'Check/replace ink'

when 'Y' also 'Y' also 'N'
    display 'Check/replace ink'
    display 'Check for paper jam'

when 'Y' also 'N' also 'Y'
    display 'Check the power cable'
    display 'Check the printer-computer cable'
    display 'Ensure printer software is installed'

when 'Y' also 'N' also 'N'
    display 'Check for paper jam'

when 'N' also 'Y' also 'Y'
    display 'Ensure printer software is installed'
    display 'Check/replace ink'

when 'N' also 'Y' also 'N'
    display 'Check/replace ink'

when 'N' also 'N' also 'Y'
    display 'Ensure printer software is installed'

when 'N' also 'N' also 'N'
    display 'no action found'

when other
    display 'invalid input: ' notprinting space flashing space notrecognized

end-evaluate

display space

stop run
.

end program 'decisiontable'.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
