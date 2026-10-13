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


def test_caught_unsupported_at_import_still_fails(fake_cobol, tmp_path):
    from cobol_equiv.harness.check import load_module, load_module_from_source

    src = textwrap.dedent("""\
        from cobol_equiv.runtime import Edited, Storage
        try:
            W = Storage("W", [Edited("E", "-$$$9.99")])
        except Exception:
            W = None
        def main(stdin, files):
            return b"HELLO\\n", {}
        """)
    path = tmp_path / "tr_import.py"
    path.write_text(src, encoding="utf-8")
    spec, exe = fake_cobol
    for mod in (load_module(path, "tr_import"), load_module_from_source(src, "tr_src", "tr_src.py")):
        d = run_once(spec, exe, mod.main, {})
        assert d is not None and d.unsupported and "imported" in d.detail


def test_unsupported_then_other_error_is_unsupported(fake_cobol):
    spec, exe = fake_cobol

    def main(stdin, files):
        try:
            Storage("W", [Edited("E", "-$$$9.99")])
        except Exception:
            pass
        raise ValueError("later failure")

    d = run_once(spec, exe, main, {})
    assert d is not None and d.unsupported and "ValueError" in d.detail


@pytest.mark.oracle
@pytest.mark.parametrize("layout", ["helper_module", "partial"])
def test_import_time_unsupported_when_main_is_elsewhere(tmp_path, capsys, monkeypatch, layout):
    """main defined in another module, or wrapped in functools.partial: the
    import-time hit is taken from the loaded module, not from main."""
    from cobol_equiv.harness.check import main

    prog = tmp_path / "prog"
    prog.mkdir()
    (prog / "program.cob").write_text(
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. P.\n"
        "       PROCEDURE DIVISION.\n"
        '           DISPLAY "HELLO"\n'
        "           STOP RUN.\n", encoding="utf-8")
    (prog / "spec.py").write_text(
        "from pathlib import Path\n"
        "from cobol_equiv.harness.spec import ProgramSpec\n"
        'SPEC = ProgramSpec("p", "test", Path(__file__).parent / "program.cob", vectors=[{}])\n',
        encoding="utf-8")
    hidden = (
        "from cobol_equiv.runtime import Edited, Storage\n"
        "try:\n"
        '    W = Storage("W", [Edited("E", "-$$$9.99")])\n'
        "except Exception:\n"
        "    W = None\n")
    tr = tmp_path / "tr.py"
    if layout == "helper_module":
        name = f"helper_mod_{tmp_path.name}"
        (tmp_path / f"{name}.py").write_text(
            hidden + "def main(stdin, files):\n    return b'HELLO\\n', {}\n", encoding="utf-8")
        monkeypatch.syspath_prepend(str(tmp_path))
        tr.write_text(f"from {name} import main\n", encoding="utf-8")
    else:
        tr.write_text(hidden + "import functools\n"
                      "def _main(stdin, files, enc):\n    return b'HELLO\\n', {}\n"
                      "main = functools.partial(_main, enc='x')\n", encoding="utf-8")
    assert main([str(prog), str(tr), "--examples", "0"]) == 2
    assert "UNSUPPORTED" in capsys.readouterr().out
