"""LINE SEQUENTIAL and record sequential files: runtime vs GnuCOBOL."""

import subprocess

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path, version_label
from cobol_equiv.runtime.files import (LineSequentialReader, LineSequentialWriter,
                                       RecordSequentialReader, RecordSequentialWriter)

PROG = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. FILES.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-F ASSIGN TO "IN.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT OUT-F ASSIGN TO "OUT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT REC-F ASSIGN TO "REC.DAT"
               ORGANIZATION IS SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD IN-F.
       01 IN-REC PIC X(8).
       FD OUT-F.
       01 OUT-REC PIC X(10).
       FD REC-F.
       01 REC-REC PIC X(8).
       WORKING-STORAGE SECTION.
       01 EOF PIC X VALUE "N".
       PROCEDURE DIVISION.
           OPEN INPUT IN-F OUTPUT OUT-F REC-F
           PERFORM UNTIL EOF = "Y"
             READ IN-F AT END MOVE "Y" TO EOF
               NOT AT END
                 DISPLAY "[" IN-REC "]"
                 MOVE IN-REC TO OUT-REC
                 WRITE OUT-REC
                 MOVE IN-REC TO REC-REC
                 WRITE REC-REC
             END-READ
           END-PERFORM
           MOVE SPACES TO OUT-REC WRITE OUT-REC
           MOVE "  X  " TO OUT-REC WRITE OUT-REC
           CLOSE IN-F OUT-F REC-F
           STOP RUN.
"""

INPUTS = [
    b"",
    b"ABCDEFGH\nAB\n\nABCDEFGHIJKL\nXY\r\nLAST",
    b"X\rY\n  lead\ntrail   \n",
    b"\n\n",
]


@pytest.mark.oracle
@pytest.mark.parametrize("data", INPUTS)
def test_line_sequential_matches_gnucobol(tmp_path, data):
    src = tmp_path / "files.cob"
    src.write_text(PROG, encoding="utf-8")
    exe = tmp_path / "files"
    r = subprocess.run([cobc_path(), *COBC_FLAGS, "-o", str(exe), str(src)],
                       capture_output=True, env=clean_env())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    (tmp_path / "IN.DAT").write_bytes(data)
    out = subprocess.run([str(exe)], cwd=tmp_path, capture_output=True, env=clean_env())
    if version_label() != "3.1.2" and b"\r" in data.replace(b"\r\n", b""):
        # GnuCOBOL 3.2 validates LINE SEQUENTIAL data on READ (NEWS 3.2,
        # COB_LS_VALIDATE): a control character inside a record is an error
        # (status 09) and, without a FILE STATUS clause, ends the program.
        # The runtime does not model this.
        assert out.returncode != 0
        return
    assert out.returncode == 0, out.stderr

    # GnuCOBOL 3.2 returns the rest of a long line as further records
    mode = "truncate" if version_label() == "3.1.2" else "split"
    reader = LineSequentialReader(data, 8, long_lines=mode)
    lsw, rsw = LineSequentialWriter(), RecordSequentialWriter()
    stdout = b""
    while (rec := reader.read()) is not None:
        stdout += b"[" + rec + b"]\n"
        lsw.write(rec.ljust(10))
        rsw.write(rec)
    lsw.write(b" " * 10)
    lsw.write(b"  X       ")
    assert out.stdout == stdout
    assert (tmp_path / "OUT.DAT").read_bytes() == lsw.getvalue()
    assert (tmp_path / "REC.DAT").read_bytes() == rsw.getvalue()
    recs = RecordSequentialReader(rsw.getvalue(), 8)
    assert [r for r in iter(recs.read, None)] == [
        r for r in iter(LineSequentialReader(data, 8, long_lines=mode).read, None)]
