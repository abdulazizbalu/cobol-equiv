"""A translation that reaches a runtime feature outside the supported subset
must never pass: the harness reports UNSUPPORTED, also when the translation
catches the error and goes on."""

import textwrap

import pytest

from cobol_equiv.harness.check import CheckResult, run_once
from cobol_equiv.harness.spec import ProgramSpec
from cobol_equiv.runtime import Edited, Storage
from cobol_equiv.runtime.errors import Unsupported, reset_unsupported_hits, unsupported_hits


@pytest.fixture
def fake_cobol(tmp_path):
    """An 'executable' that prints what the translations below print."""
    exe = tmp_path / "prog"
    exe.write_text("#!/bin/sh\nprintf 'HELLO\\n'\n", encoding="utf-8")
    exe.chmod(0o755)
    return ProgramSpec("p", "test", tmp_path / "p.cob"), exe


def test_hits_are_counted():
    reset_unsupported_hits()
    with pytest.raises(Unsupported):
        Storage("W", [Edited("E", "-$$$9.99")])
    assert unsupported_hits() == 1


def test_raised_unsupported_is_reported(fake_cobol):
    spec, exe = fake_cobol

    def main(stdin, files):
        Storage("W", [Edited("E", "-$$$9.99")])
        return b"HELLO\n", {}

    d = run_once(spec, exe, main, {})
    assert d is not None and d.unsupported
    assert CheckResult("p", difference=d).status == "unsupported"


def test_caught_unsupported_still_fails(fake_cobol):
    spec, exe = fake_cobol

    def main(stdin, files):
        try:
            Storage("W", [Edited("E", "-$$$9.99")])
        except Exception:
            pass  # a translation that hides the problem
        return b"HELLO\n", {}  # output identical to the COBOL program

    d = run_once(spec, exe, main, {})
    assert d is not None and d.unsupported and "caught" in d.detail


def test_clean_translation_passes(fake_cobol):
    spec, exe = fake_cobol
    assert run_once(spec, exe, lambda s, f: (b"HELLO\n", {}), {}) is None


@pytest.mark.oracle
def test_cli_exit_status_for_unsupported(tmp_path, capsys):
    from cobol_equiv.harness.check import main

    prog = tmp_path / "prog"
    prog.mkdir()
    (prog / "program.cob").write_text(
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. P.\n"
        "       PROCEDURE DIVISION.\n"
        '           DISPLAY "HELLO"\n'
        "           STOP RUN.\n", encoding="utf-8")
    (prog / "spec.py").write_text(textwrap.dedent("""\
        from pathlib import Path
        from cobol_equiv.harness.spec import ProgramSpec
        SPEC = ProgramSpec("p", "test", Path(__file__).parent / "program.cob", vectors=[{}])
        """), encoding="utf-8")
    tr = tmp_path / "tr.py"
    tr.write_text(textwrap.dedent("""\
        from cobol_equiv.runtime import Edited, Storage
        def main(stdin, files):
            try:
                Storage("W", [Edited("E", "-$$$9.99")])
            except Exception:
                pass
            return b"HELLO\\n", {}
        """), encoding="utf-8")
    assert main([str(prog), str(tr), "--examples", "0"]) == 2
    assert "UNSUPPORTED" in capsys.readouterr().out
