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
input_files = {'infile.dat': b'                                                                                '}
expected stdout = b'\n'
expected output_files = {'outfile.dat': b'                                                                                '}

### Example 2
stdin = b''
input_files = {'infile.dat': b'"*R                                                                             '}
expected stdout = b'                                                                             R*"\n'
expected output_files = {'outfile.dat': b'                                                                             R*"'}

## COBOL program
```cobol
       identification division.
       program-id. lrecl80.

       environment division.
       configuration section.
       repository.
           function all intrinsic.

       input-output section.
       file-control.
           select infile
               assign to infile-name
               organization is sequential
               file status is infile-status
           .
           select outfile
               assign to outfile-name
               organization is sequential
               file status is outfile-status
           .

       data division.
       file section.
       fd infile.
           01 input-text pic x(80).

       fd outfile.
           01 output-text pic x(80).

       working-storage section.
       01 infile-name.
          05 value "infile.dat".
       01 infile-status pic xx.
          88 ok-input value '00'.
          88 eof-input value '10'.

       01 outfile-name.
          05 value "outfile.dat".
       01 outfile-status pic xx.
          88 ok-output value '00'.

       procedure division.

       open input infile
       if not ok-input then
           display "error opening input " infile-name upon syserr
           goback
       end-if

       open output outfile
       if not ok-output
           display "error opening output " outfile-name upon syserr
           goback
       end-if

       read infile
       perform until not ok-input
           move function reverse(input-text) to output-text

           write output-text
           if not ok-output then
               display "error writing: " output-text upon syserr
           end-if
           read infile
       end-perform

       close infile outfile

       open input outfile
       if not ok-output then
           display "error opening input " outfile-name upon syserr
           goback
       end-if

       read outfile
       perform until not ok-output
           display function trim(output-text trailing)
           read outfile
       end-perform

       close outfile

       goback.
       end program lrecl80.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
