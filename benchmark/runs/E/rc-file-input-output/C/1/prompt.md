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
input_files = {'input.txt': b'                                                                                '}
expected stdout = b''
expected output_files = {'output.txt': b'                                                                                '}

### Example 2
stdin = b''
input_files = {'input.txt': b']                                                                               '}
expected stdout = b''
expected output_files = {'output.txt': b']                                                                               '}

## COBOL program
```cobol
       identification division.
       program-id. copyfile.
       environment division.
       input-output section.
       file-control.
           select input-file assign to "input.txt"
               organization sequential
           .
           select output-file assign to "output.txt"
               organization sequential
           .
       data division.
       file section.
       fd input-file.
       1 input-record pic x(80).
       fd output-file.
       1 output-record pic x(80).
       working-storage section.
       1 end-of-file-flag pic 9 value 0.
         88 eof value 1.
       1 text-line pic x(80).
       procedure division.
       begin.
           open input input-file
               output output-file
           perform read-input
           perform until eof
               write output-record from text-line
               perform read-input
           end-perform
           close input-file output-file
           stop run
           .
       read-input.
           read input-file into text-line
           at end
               set eof to true
           end-read
           .
       end program copyfile.
```

Reply with the complete Python module in one ```python code block. Do not
write anything after the code block.
