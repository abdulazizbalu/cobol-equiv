# omp-cbl0001

Source: Open Mainframe Project, COBOL Programming Course, commit
`1f037d24326124f4f2c5cd2d31e5220ceb549580`, file
`COBOL Programming Course #2 - Learning COBOL/Labs/cbl/CBL0001.cobol`
(copied unchanged as `original.cob`). License: CC BY 4.0
(`../LICENSE-OMP-CC-BY-4.0.txt`), copyright Contributors to the COBOL
Programming Course.

Changes in `program.cob`:

- line 7: a period added after `PROGRAM-ID.    CBL0001` (GnuCOBOL's default
  dialect requires it; see deviation D1 in `docs/benchmark-protocol.md`).

Files: ACCTREC (input) and PRTLINE (output) keep their ASSIGN names and the
default ORGANIZATION SEQUENTIAL (fixed-length records).

Generator overrides: none.

Fixed vector: the course's sample data set `Labs/data/data` (45 records of
170 bytes, EBCDIC). `sample-ACCTREC.bin` is that file with the text fields
(bytes 1-8 and 19-170 of each record) converted from EBCDIC (code page 037)
to ASCII and the two COMP-3 fields (bytes 9-18) copied unchanged.
