import subprocess

import pytest

from cobol_equiv.cobc import COBC_FLAGS, clean_env, cobc_path, cobc_version

HELLO = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO.
       PROCEDURE DIVISION.
           DISPLAY "HELLO"
           STOP RUN.
"""


@pytest.mark.oracle
def test_cobc_compiles_and_runs(tmp_path):
    assert "GnuCOBOL" in cobc_version()
    src = tmp_path / "hello.cob"
    src.write_text(HELLO, encoding="utf-8")
    exe = tmp_path / "hello"
    subprocess.run(
        [cobc_path(), *COBC_FLAGS, "-o", str(exe), str(src)],
        check=True, capture_output=True, env=clean_env(),
    )
    out = subprocess.run([str(exe)], check=True, capture_output=True, env=clean_env())
    assert out.stdout == b"HELLO\n"
