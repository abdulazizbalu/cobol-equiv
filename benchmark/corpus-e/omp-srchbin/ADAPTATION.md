# omp-srchbin

Source: Open Mainframe Project, COBOL Programming Course, commit
`1f037d24326124f4f2c5cd2d31e5220ceb549580`, file
`COBOL Programming Course #2 - Learning COBOL/Labs/cbl/SRCHBIN.cobol`
(copied unchanged as `original.cob`). License: CC BY 4.0
(`../LICENSE-OMP-CC-BY-4.0.txt`), copyright Contributors to the COBOL
Programming Course.

Changes in `program.cob`:

- none.

Files: ACCTREC (input) keeps its ASSIGN name and the default ORGANIZATION
SEQUENTIAL (fixed-length records).

Input layout used for generation: the table entry layout of the program
(the FD declares the record as `PIC X(170)`).

Generator overrides: none. Generated inputs therefore almost never contain
the searched value; the outputs on HELD-OUT are mostly the "not found" line.

Fixed vector: the course's sample data set `Labs/data/data` (45 records of
170 bytes, EBCDIC). `sample-ACCTREC.bin` is that file with the text fields
(bytes 1-8 and 19-170 of each record) converted from EBCDIC (code page 037)
to ASCII and the two COMP-3 fields (bytes 9-18) copied unchanged.
