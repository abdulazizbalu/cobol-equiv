"""Benchmark corpus, vectors, prompts and translation driver
(docs/benchmark-protocol.md). No translator is called here."""

import csv
import gzip
import json
from pathlib import Path

import pytest

from cobol_equiv.benchmark import apisheet, fetch, prompts, translate
from cobol_equiv.benchmark.programs import programs
from cobol_equiv.benchmark.vectors import (N_VISIBLE, PRIMARY, build_sets, decode_input, load,
                                           unb64, vectors_path)

ROOT = Path(__file__).resolve().parent.parent
TRACKS = {"E": programs("E"), "R": programs("R")}
ALL = TRACKS["E"] + TRACKS["R"]


def fetched(p):
    return Path(p.spec().source).exists()


def test_corpus_sizes_match_the_screening_record():
    with (ROOT / "benchmark" / "corpus-e" / "screening.csv").open(encoding="utf-8", newline="") as fh:
        kept = [r for r in csv.DictReader(fh) if r["result"] == "kept"]
    assert len(TRACKS["E"]) == len(kept) <= 30
    assert len(TRACKS["R"]) == 20
    assert len({p.name for p in ALL}) == len(ALL)


def test_every_program_has_committed_vectors_for_both_compilers():
    for p in ALL:
        doc = load(p)
        assert doc["program"] == p.name and doc["track"] == p.track
        assert len(doc["sets"]["visible"]) == N_VISIBLE, p.name
        held, lost = len(doc["sets"]["heldout"]), sum(r["set"] == "heldout" for r in doc["removed"])
        assert held > 0 and lost * 10 <= held + lost, p.name
        for items in doc["sets"].values():
            for v in items:
                assert PRIMARY in v["expected"] and "3.2" in v["expected"], p.name


def test_sets_are_disjoint():
    for p in ALL:
        doc = load(p)
        seen = set()
        for items in doc["sets"].values():
            for v in items:
                key = json.dumps(v["input"], sort_keys=True)
                assert key not in seen, p.name
                seen.add(key)


def test_vector_files_hold_canonical_json():
    """Sorted keys and fixed indentation, so a rewrite gives the same text.
    (The gzip bytes also depend on the zlib build; the CI benchmark job
    compares them on Python 3.12.)"""
    for p in ALL:
        text = gzip.decompress(vectors_path(p).read_bytes()).decode("utf-8")
        assert json.dumps(json.loads(text), indent=1, sort_keys=True) + "\n" == text, p.name


def _pinned_hypothesis():
    import hypothesis

    pins = (ROOT / "requirements-repro.txt").read_text(encoding="utf-8")
    return f"hypothesis=={hypothesis.__version__}" in pins


@pytest.mark.skipif(not _pinned_hypothesis(), reason="generation is pinned to the Hypothesis version "
                    "in requirements-repro.txt")
@pytest.mark.parametrize("name", ["acctpost", "tables", "rc-a-plus-b", "omp-srchser"])
def test_generated_sets_match_the_committed_ones(name):
    p = next(p for p in ALL if p.name == name)
    doc = load(p)
    sets = build_sets(p.spec())
    for set_name in ("visible", "dev"):
        committed = [decode_input(v["input"]) for v in doc["sets"][set_name]]
        removed = [decode_input(r["input"]) for r in doc["removed"] if r["set"] == set_name]
        assert [inp for _, inp in sets[set_name] if inp not in removed] == committed


def test_shown_source_removes_comments_only():
    fixed = ("000100 IDENTIFICATION DIVISION.".ljust(72) + "SEQ00001\n"
             "      * a comment line\n"
             "      / a page eject\n"
             '           DISPLAY "A *> B" *> trailing comment\n'
             "\n"
             "           STOP RUN.\n")
    assert prompts.shown_source(fixed, free=False) == (
        "000100 IDENTIFICATION DIVISION.\n"
        '           DISPLAY "A *> B"\n'
        "\n"
        "           STOP RUN.\n")
    free = "*> header\nprogram-id. x. *> note\n  display 'a*>b'.\n"
    assert prompts.shown_source(free, free=True) == "program-id. x.\n  display 'a*>b'.\n"


def test_extract_code():
    assert translate.extract_code("x\n```python\na = 1\n```\n") == "a = 1\n"
    assert translate.extract_code("```\nb = 2\n```\n```python\nc = 3\n```\n") == "c = 3\n"
    assert translate.extract_code("```py\nd = 4\n```\n") == "d = 4\n"
    assert translate.extract_code("no code") is None
    assert translate.extract_code(None) is None


def test_api_sheet_is_the_committed_one():
    assert apisheet.generate() == apisheet.SHEET.read_text(encoding="utf-8")


def test_api_sheet_has_no_statement_from_the_findings():
    text = apisheet.SHEET.read_text(encoding="utf-8").lower()
    for word in ("gnucobol", "negative zero", "remainder is", "trailing sign", "findings", "trap",
                 "mutant", "half away"):
        assert word not in text, word


def test_adaptation_edits_must_match_once():
    assert fetch.adapt("A B A", [["B", "C"]]) == "A C A"
    with pytest.raises(ValueError):
        fetch.adapt("A B A", [["A", "C"]])
    with pytest.raises(ValueError):
        fetch.adapt("A B A", [["X", "C"]])


def test_translator_command_has_no_tools_and_no_settings():
    cmd = translate.client_command("m")
    for flag in ("--safe-mode", "--strict-mcp-config", "--no-session-persistence",
                 "--disable-slash-commands"):
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--setting-sources") + 1] == ""
    assert cmd[cmd.index("--model") + 1] == "m"


def test_prompts_show_only_visible_vectors():
    p = next(p for p in ALL if p.name == "acctpost")
    a, c = prompts.prompt_one_shot(p, "A"), prompts.prompt_one_shot(p, "C")
    assert "## API reference: cobol_equiv.runtime" in a and "API reference" not in c
    assert "cobol_equiv" not in c
    doc = load(p)
    for v in doc["sets"]["visible"]:
        assert repr(unb64(v["expected"][PRIMARY]["stdout"])) in a
    for v in doc["sets"]["heldout"][:20]:
        out = unb64(v["expected"][PRIMARY]["stdout"])
        if len(out) > 40:
            assert repr(out) not in a


def test_shown_sources_have_no_comments():
    for p in ALL:
        if not fetched(p):
            pytest.skip("Track E sources not fetched (python -m cobol_equiv.benchmark.fetch)")
        assert "*>" not in prompts.source_of(p), p.name


def test_runner_test_program_is_outside_both_tracks():
    names = {p.name for p in ALL}
    assert programs("T") and all(p.name not in names for p in programs("T"))


def test_statistics():
    from cobol_equiv.benchmark.analysis import binom_two_sided, holm, mcnemar, wilson

    lo, hi = wilson(5, 10)
    assert round(lo, 4) == 0.2366 and round(hi, 4) == 0.7634
    assert wilson(0, 0) == (0.0, 1.0)
    assert binom_two_sided(1, 10) == 22 / 1024
    assert binom_two_sided(0, 0) == 1.0 and binom_two_sided(5, 10) == 1.0
    assert holm([0.01, 0.04, 0.03, 0.2]) == [0.04, 0.09, 0.09, 0.2]
    m = mcnemar([(True, False)] * 6 + [(True, True)] * 3 + [(False, True)])
    assert (m["first_only"], m["second_only"]) == (6, 1) and m["p"] == binom_two_sided(1, 7)


def test_committed_artifacts_are_consistent_with_the_manifest():
    from cobol_equiv.benchmark import audit

    if not (audit.RUNS / "E").exists():
        pytest.skip("no translation runs committed")
    if not all(fetched(p) for p in ALL):
        pytest.skip("Track E sources not fetched (python -m cobol_equiv.benchmark.fetch)")
    problems, suspects, counts = audit.check()
    assert problems == []
    assert counts["prompts_rebuilt"] == 2 * 3 * len(ALL)


def test_verify_covers_every_attempt():
    from cobol_equiv.benchmark import verify

    if not (verify.RUNS / "E").exists():
        pytest.skip("no translation runs committed")
    assert len(verify.units()) == 3 * 3 * len(ALL)
    if verify.OUT.exists():
        with verify.OUT.open(encoding="utf-8", newline="") as fh:
            got = {(r["track"], r["program"], r["condition"], int(r["attempt"])) for r in csv.DictReader(fh)}
        assert got == set(verify.units())


SLOW_TRANSLATION = """
import time

def main(stdin, input_files):
    time.sleep(float(stdin or b"0"))
    return b"done " + stdin + b"\\n", {}
"""


def test_total_limit_keeps_finished_vectors(tmp_path):
    from cobol_equiv.benchmark.runner import run_translation

    t = tmp_path / "t.py"
    t.write_text(SLOW_TRANSLATION, encoding="utf-8")
    inputs = [{"<stdin>": b"0"}, {"<stdin>": b"30"}, {"<stdin>": b"0"}]
    res = run_translation(t, inputs, timeout=60, condition="A", total=3)
    assert "stdout" in res[0]
    assert res[1].get("timeout") and res[2].get("timeout")


def test_slow_but_correct_vector_passes_under_the_extended_limit(tmp_path, monkeypatch):
    from cobol_equiv.benchmark import runner

    t = tmp_path / "t.py"
    t.write_text(SLOW_TRANSLATION, encoding="utf-8")
    monkeypatch.setattr(runner, "EXTENDED_TIMEOUT", 10)
    monkeypatch.setattr(runner, "EXTENDED_TOTAL", 30)
    res = runner.run_extended(t, [{"<stdin>": b"0"}, {"<stdin>": b"2"}], timeout=1, condition="A")
    assert "stdout" in res[1] and res[1]["slow"] and not res[0].get("slow")


def test_extended_run_stops_after_repeated_timeouts(tmp_path, monkeypatch):
    from cobol_equiv.benchmark import runner

    t = tmp_path / "t.py"
    t.write_text(SLOW_TRANSLATION, encoding="utf-8")
    monkeypatch.setattr(runner, "EXTENDED_TIMEOUT", 1)
    monkeypatch.setattr(runner, "EXTENDED_MAX_TIMEOUTS", 2)
    res = runner.run_extended(t, [{"<stdin>": b"30"}] * 4, timeout=1, condition="A")
    assert all(r.get("timeout") for r in res)
    assert [bool(r.get("not_rerun")) for r in res] == [False, False, True, True]


SWALLOWING_TRANSLATION = """
import time

def main(stdin, input_files):
    if stdin == b"loop":
        while True:
            try:
                time.sleep(100)
            except BaseException:
                pass
    return b"ok\\n", {}
"""


def test_a_swallowed_timeout_still_ends_the_vector(tmp_path):
    from cobol_equiv.benchmark.runner import run_translation

    t = tmp_path / "t.py"
    t.write_text(SWALLOWING_TRANSLATION, encoding="utf-8")
    res = run_translation(t, [{"<stdin>": b""}, {"<stdin>": b"loop"}, {"<stdin>": b""}], timeout=1,
                          condition="A", total=60)
    assert "stdout" in res[0]
    assert res[1].get("timeout") and res[2].get("timeout") and res[2].get("abandoned")


def test_slow_module_load_is_a_timeout(tmp_path):
    from cobol_equiv.benchmark.runner import run_translation

    t = tmp_path / "t.py"
    t.write_text("import time\ntime.sleep(30)\ndef main(s, f):\n    return b'', {}\n", encoding="utf-8")
    res = run_translation(t, [{"<stdin>": b""}] * 2, timeout=1, condition="A", total=60)
    assert all(r.get("timeout") for r in res)


def test_crashed_process_and_extra_results(tmp_path):
    from cobol_equiv.benchmark.runner import run_translation

    t = tmp_path / "t.py"
    t.write_text("import os\ndef main(s, f):\n    os._exit(3)\n", encoding="utf-8")
    res = run_translation(t, [{"<stdin>": b""}] * 2, timeout=5, condition="A", total=60)
    assert all("ended without a result" in r["error"] for r in res)


def _fake_evaluate(monkeypatch, results):
    from cobol_equiv.benchmark import verify
    from cobol_equiv.benchmark.vectors import b64

    monkeypatch.setattr(verify, "_results", lambda path, condition, items, timeout, mode: results)
    p = next(p for p in ALL if p.name == "acctpost")
    exp = {"3.1.2": {"stdout": b64(b"x\n"), "files": {}}}
    items = [{"input": {}, "expected": exp} for _ in results]
    return verify._evaluate(p, Path(__file__), "A", items, "3.1.2", "registered")


def test_timeout_precedence(monkeypatch):
    from cobol_equiv.benchmark.vectors import b64

    ok, slow = {"stdout": b64(b"x\n"), "files": {}}, {"stdout": b64(b"x\n"), "files": {}, "slow": True}
    bad, late = {"stdout": b64(b"y\n"), "files": {}}, {"timeout": True}
    r = _fake_evaluate(monkeypatch, [ok, late, bad])
    assert (r["pass"], r["first_failure_kind"], r["timeout_vectors"]) == (0, "difference", 1)
    r = _fake_evaluate(monkeypatch, [ok, late])
    assert (r["pass"], r["first_failure_kind"]) == (0, "timeout")
    r = _fake_evaluate(monkeypatch, [ok, slow])
    assert (r["pass"], r["slow_vectors"], r["first_failure_kind"]) == (1, 1, "")


def test_verify_compare_ignores_machine_dependent_counts():
    from cobol_equiv.benchmark import verify

    head = ",".join(verify.FIELDS) + "\n"
    a = head + "E,p,A,1,0,3.1.2,heldout,3,3,1,1,0,,,t\n"
    b = head + "E,p,A,1,0,3.1.2,heldout,3,3,1,0,0,,,t\n"
    c = head + "E,p,A,1,0,3.1.2,heldout,3,2,0,0,0,difference,x,t\n"
    assert verify.compare(a, b) == []
    assert len(verify.compare(a, c)) == 1


def test_b_versions_carry_the_last_code_forward():
    from cobol_equiv.benchmark import verify

    for p in ALL:
        for attempt in (1, 2, 3):
            vs = verify.versions(p, "B", attempt)
            if vs is None:
                continue
            assert len(vs) == 4
            fin = json.loads((verify.RUNS / p.track / p.name / "B" / str(attempt) / "final.json")
                             .read_text(encoding="utf-8"))
            last = vs[-1]
            assert (None if last is None else last.relative_to(ROOT).as_posix()) == fin["final"]


def test_report_parts_come_from_the_failures_file():
    from cobol_equiv.benchmark import analysis

    if not analysis.FAILURES.exists():
        pytest.skip("no failures.csv committed")
    with analysis.FAILURES.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert all(r["category"] in analysis.CATEGORIES for r in rows)
    crashes = analysis.crash_messages()
    assert sum(n for _, n in crashes) == sum(r["category"] == "crash or syntax error" for r in rows)
    ex = dict(analysis.examples())
    assert set(ex) == {r["category"] for r in rows}
    block = analysis.tables(analysis.compute(analysis.load_verdicts()))
    for cat, (num, anchor) in analysis.TRAPS.items():
        if cat in ex:
            assert f"{analysis.TRAPS_LINK}#{anchor}" in block
            assert f"### {num}." in (ROOT / "docs" / "semantic-traps.md").read_text(encoding="utf-8")


def test_report_check_fails_without_the_generated_block(tmp_path, monkeypatch):
    from cobol_equiv.benchmark import analysis

    if not analysis.VERDICTS.exists():
        pytest.skip("no verdicts committed")
    doc = tmp_path / "benchmark.md"
    doc.write_text("no block here\n", encoding="utf-8")
    monkeypatch.setattr(analysis, "DOC", doc)
    assert analysis.report(check=True) == 1


COMPARING_TRANSLATION = """\
from cobol_equiv.runtime import dec

def main(stdin, files):
    a, b = dec("1.50"), dec("1.5")
    out = [a == b, a != b, a == a, dec(2) == 2, hash(a) == hash(b)]
    if stdin == b"order":
        out.append(a < dec(2))
    return repr(out).encode("ascii"), {}
"""


def test_driver_runtime_modes(tmp_path):
    """registered: CobDecimal as in runtime 1.0.0 (identity ==, no ordering);
    corrected: value comparison; both count the calls (D14)."""
    from cobol_equiv.benchmark.runner import run_translation
    from cobol_equiv.benchmark.vectors import unb64

    t = tmp_path / "t.py"
    t.write_text(COMPARING_TRANSLATION, encoding="utf-8")
    inputs = [{"<stdin>": b""}, {"<stdin>": b"order"}]
    reg = run_translation(t, inputs, timeout=10, condition="A", runtime="registered")
    cor = run_translation(t, inputs, timeout=10, condition="A", runtime="corrected")
    assert unb64(reg[0]["stdout"]) == b"[False, True, True, False, False]"
    assert reg[1]["error"] == "TypeError: '<' not supported between instances of 'CobDecimal' and 'CobDecimal'"
    assert unb64(cor[0]["stdout"]) == b"[True, False, True, True, True]"
    assert unb64(cor[1]["stdout"]) == b"[True, False, True, True, True, True]"
    # a == b, a != b and dec(2) == 2 answer differently in the two modes; a == a does not
    for r in (reg[0], cor[0]):
        assert (r["cmp"]["eq"], r["cmp"]["eq_diff"], r["cmp"]["hash"]) == (4, 3, 2)
    assert reg[1]["cmp"]["order"] == cor[1]["cmp"]["order"] == 1
    # without a mode the installed runtime is used and nothing is counted
    plain = run_translation(t, inputs[:1], timeout=10, condition="A")
    assert unb64(plain[0]["stdout"]) == unb64(cor[0]["stdout"]) and not any(plain[0]["cmp"].values())


REGISTERED_PROBE = """\
from decimal import Decimal
from cobol_equiv.runtime import dec

def main(stdin, files):
    a, b = dec(1), dec(1)
    out = [a == b, a != b, a == a, a != a, a == 1, 1 == a, a != 1, a == Decimal(1), Decimal(1) == a,
           a == "1", a == None, hash(a) == object.__hash__(a)]
    for x, y in ((a, b), (a, 1), (1, a), (a, Decimal(1)), (a, "1")):
        try:
            x < y
            out.append("no error")
        except TypeError as e:
            out.append(str(e))
    return repr(out).encode("ascii"), {}
"""


def test_registered_mode_is_runtime_1_0_0(tmp_path):
    """Registered mode: CobDecimal behaves as a class without comparison
    methods (runtime 1.0.0), with the same reflected fallbacks and messages."""
    from cobol_equiv.benchmark.runner import run_translation
    from cobol_equiv.benchmark.vectors import unb64

    t = tmp_path / "t.py"
    t.write_text(REGISTERED_PROBE, encoding="utf-8")
    r = run_translation(t, [{"<stdin>": b""}], timeout=10, condition="A", runtime="registered")[0]
    msg = "'<' not supported between instances of '{}' and '{}'"
    expected = [False, True, True, False, False, False, True, False, False, False, False, True,
                msg.format("CobDecimal", "CobDecimal"), msg.format("CobDecimal", "int"),
                msg.format("int", "CobDecimal"), msg.format("CobDecimal", "decimal.Decimal"),
                msg.format("CobDecimal", "str")]
    assert unb64(r["stdout"]).decode("ascii") == repr(expected)


def test_eqscan_finds_comparison_sites():
    from cobol_equiv.benchmark.eqscan import scan

    src = (
        "from cobol_equiv.runtime import dec as D\n"
        "def total(ws):\n    return D(ws['A']) + 1\n"
        "def main(stdin, files):\n"
        "    x = D(1)\n"
        "    if x == 0: pass\n"
        "    if total(None) != D(2): pass\n"
        "    while D(3) < x: pass\n"
        "    s = {x}\n"
        "    if x in s: pass\n"
        "    y = max(x, D(4))\n"
        "    if 1 == 2: pass\n"
        "    if x.to_decimal() == 0: pass\n"
    )
    kinds = [(line, kind) for line, kind, _ in scan(src)]
    assert kinds == [(6, "eq"), (7, "eq"), (8, "order"), (9, "hash"), (10, "in"), (11, "order")]


def test_ci_sample_is_fixed_and_stratified():
    from cobol_equiv.benchmark import ci, verify

    us = verify.units()
    a, b = ci.sample(us, 2), ci.sample(list(us), 2)
    assert a == b and len(a) == 12
    strata = {(u[0], u[2]) for u in a}
    assert strata == {(t, c) for t in "ER" for c in "ABC"}


def test_ci_input_hash_keys(monkeypatch):
    from cobol_equiv.benchmark import ci, verify

    a = next(u for u in verify.units() if u[2] == "A")
    c = next(u for u in verify.units() if u[2] == "C")
    assert ci.input_hash(a, "registered") != ci.input_hash(a, "corrected")
    assert ci.input_hash(c, "registered") == ci.input_hash(c, "corrected")
    before = ci.input_hash(a, "corrected"), ci.input_hash(c, "corrected")
    monkeypatch.setattr(ci, "runtime_version", lambda: "0.0.0-test")
    assert ci.input_hash(a, "corrected") != before[0] and ci.input_hash(c, "corrected") == before[1]


def test_corrected_verdicts_differ_only_inside_the_d14_scope():
    """Outside the D14 scope, verdicts-corrected.csv holds the registered rows;
    the sample units have the same verdicts in both modes; the comparisons
    files cover exactly the scope."""
    from cobol_equiv.benchmark import ci, verify

    reg = ci._rows_by_unit(verify.OUT.read_text(encoding="utf-8"))
    cor = ci._rows_by_unit(verify.OUTS["corrected"][0].read_text(encoding="utf-8"))
    affected, sampled = ci.scope()
    assert set(reg) == set(cor)
    for u in verify.units():
        i = ci.unit_id(u)
        if u not in affected and u not in sampled:
            assert reg[i] == cor[i], i
        elif u in sampled:
            assert [r["pass"] for r in reg[i]] == [r["pass"] for r in cor[i]], i
    scope_ids = {ci.unit_id(u) for u in affected + sampled}
    for out in (verify.OUTS["registered"][1], verify.OUTS["corrected"][1]):
        assert set(ci._rows_by_unit(out.read_text(encoding="utf-8"))) == scope_ids
    assert ci.c_uses_runtime() == []


def test_ci_check_compares_with_the_committed_rows(monkeypatch):
    """ci.check on rows equal to the committed ones passes and a changed
    verdict fails (units are not run: run_units returns committed rows)."""
    from cobol_equiv.benchmark import ci, verify

    def fake(changed=None):
        def run_units(units, mode, jobs, progress):
            committed = ci._rows_by_unit(verify.OUTS[mode][0].read_text(encoding="utf-8"))
            usage = ci._rows_by_unit(verify.OUTS[mode][1].read_text(encoding="utf-8"))
            out = {}
            for u in units:
                rows = [dict(r) for r in committed[ci.unit_id(u)]]
                counts = {(r["round"]): r for r in usage.get(ci.unit_id(u), [])}
                for r in rows:
                    c = counts.get(r["round"]) if r["set"] == "heldout" and r["version"] == verify.PRIMARY else None
                    for k in verify.CMP:
                        r[k] = c[k] if c else "0"
                    if changed and ci.unit_id(u) == changed:
                        r["pass"] = "1" if r["pass"] == "0" else "0"
                out[u] = rows
            return out
        return run_units

    for mode in verify.MODES:
        monkeypatch.setattr(ci, "run_units", fake())
        assert ci.check(mode, "R", None, 2, 1, lambda m: None) == 0
    unit = next(u for u in ci.scope()[0] if u[0] == "R")
    monkeypatch.setattr(ci, "run_units", fake(ci.unit_id(unit)))
    assert ci.check("corrected", "R", None, 2, 1, lambda m: None) == 1


def test_unit_key_covers_the_spec(tmp_path, monkeypatch):
    """A change of the program's spec.py changes the key of its saved units,
    so verdicts made under the old spec are not reused."""
    import shutil

    from cobol_equiv.benchmark import verify
    from cobol_equiv.benchmark.programs import Program

    unit = next(u for u in verify.units() if u[0] == "R" and u[2] == "A")
    p = verify._program(unit[0], unit[1])
    copy = tmp_path / p.dir.name
    shutil.copytree(p.dir, copy, ignore=shutil.ignore_patterns("__pycache__"))
    fake = Program(p.track, copy)
    monkeypatch.setattr(verify, "_program", lambda track, name: fake)
    before = verify.unit_key(unit)
    (copy / "spec.py").write_text((copy / "spec.py").read_text(encoding="utf-8") + "\n# changed\n",
                                  encoding="utf-8")
    assert verify.unit_key(unit) != before


IMPORT_TIME_COMPARISON = """\
from cobol_equiv.runtime import dec

SAME = dec("1.0") == dec(1)

def main(stdin, files):
    return repr(SAME).encode("ascii"), {}
"""


def test_import_time_comparisons_are_counted(tmp_path):
    from cobol_equiv.benchmark.runner import run_translation
    from cobol_equiv.benchmark.vectors import unb64

    t = tmp_path / "t.py"
    t.write_text(IMPORT_TIME_COMPARISON, encoding="utf-8")
    for mode, value in (("registered", b"False"), ("corrected", b"True")):
        res = run_translation(t, [{"<stdin>": b""}] * 2, timeout=10, condition="A", runtime=mode)
        for r in res:
            assert unb64(r["stdout"]) == value
            assert (r["cmp"]["eq"], r["cmp"]["eq_diff"]) == (1, 1)
