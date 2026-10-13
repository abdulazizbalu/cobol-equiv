"""Checks behind the mutants marked `equivalent` (docs/mutants.md).

Where the input domain of the mutated statement is small, the reference and
the mutated code are run on every value of it; the remaining claims rest on
the arguments in docs/mutants.md. The last tests check that no equivalence
claim is contradicted by the committed mutation run, and show the input that
made ctlbreak/float-total lose its "equivalent" label.
"""

import csv
import textwrap
from decimal import Decimal
from pathlib import Path

import pytest

from cobol_equiv.harness.corpus import (load_mutants, load_mutated, load_reference, load_spec,
                                        program_dirs)
from cobol_equiv.runtime import Storage, move

ROOT = Path(__file__).resolve().parent.parent
DIRS = {d.name: d for d in program_dirs()}

EQUIVALENT = {
    ("classify", "float-compare"), ("datecalc", "python-floor-division"),
    ("datecalc", "year-unsigned-ignored"), ("loancalc", "mrate-half-even"),
    ("loancalc", "residual-abs"), ("loancalc", "loop-limit-gt"),
    ("payroll", "overtime-ge-40"), ("payroll", "bracket-lt"), ("tables", "rank-sign"),
}


def mutant(program, mid):
    return next(m for m in load_mutants(DIRS[program]) if m["id"] == mid)


def modules(program, mid):
    return load_reference(DIRS[program]), load_mutated(DIRS[program], mutant(program, mid))


def statement(code):
    return compile(textwrap.dedent(code), "<statement>", "exec")


def test_equivalent_labels_match_this_file():
    labelled = {(d.name, m["id"]) for d in DIRS.values() for m in load_mutants(d) if m.get("equivalent")}
    assert labelled == EQUIVALENT


def test_every_equivalent_mutant_is_justified_in_docs():
    text = (ROOT / "docs" / "mutants.md").read_text(encoding="utf-8")
    for program, mid in EQUIVALENT:
        assert f"`{program}/{mid}`" in text


def test_loancalc_mrate_half_even_all_rates():
    """LN-RATE 99V999: every value 0.000 .. 99.999."""
    ref, mut = modules("loancalc", "mrate-half-even")
    find, repl = mutant("loancalc", "mrate-half-even")["edits"][1]
    s_ref, s_mut = statement(find), statement(repl)
    ln, ws_a, ws_b = Storage("LN", ref.LOAN_REC), ref.working_storage(), ref.working_storage()
    for k in range(100000):
        move(Decimal(k).scaleb(-3), ln["LN-RATE"])
        exec(s_ref, vars(ref), {"ln": ln, "ws": ws_a})  # noqa: S102
        exec(s_mut, vars(mut), {"ln": ln, "ws": ws_b})  # noqa: S102
        assert ws_a["WS-MRATE"].raw == ws_b["WS-MRATE"].raw, k


def test_tables_rank_sign_all_quantities():
    """WS-QTY 9(5): every value 0 .. 99999."""
    ref, mut = modules("tables", "rank-sign")
    find, repl = mutant("tables", "rank-sign")["edits"][0]
    s_ref, s_mut = statement(find), statement(repl)
    ws = ref.working_storage()
    for q in range(100000):
        move(q, ws.f("WS-QTY", 1))
        exec(s_ref, vars(ref), {"ws": ws, "i": 1})  # noqa: S102
        a = ws["WL-QTY"].raw
        exec(s_mut, vars(mut), {"ws": ws, "i": 1})  # noqa: S102
        assert ws["WL-QTY"].raw == a, q


class Payroll:
    """One employee record at a time through pay_one, storage kept between
    calls as in the program (so the running totals are compared too)."""

    def __init__(self, module):
        from cobol_equiv.runtime.files import RecordSequentialWriter

        self.m = module
        self.e = Storage("EMP-REC", module.EMP_REC)
        self.pay = Storage("PAY-REC", module.PAY_REC)
        self.ws, self.pf = module.working_storage(), RecordSequentialWriter()
        move("E0001", self.e["EMP-ID"])
        move("A", self.e["EMP-DED-CODE"])
        move(0, self.e["EMP-ADJUST"])

    def __call__(self, hours, rate):
        move(Decimal(hours), self.e["EMP-HOURS"])
        move(Decimal(rate), self.e["EMP-RATE"])
        out = bytearray()
        self.m.pay_one(self.e, self.ws, self.pay, out, self.pf)
        return (bytes(out), bytes(self.pay.area), bytes(self.ws.area)), self.ws["WS-GROSS"].value


def test_payroll_overtime_ge_40_all_rates_at_40_hours():
    """The mutant changes only which branch of the hours test runs, and only
    at EMP-HOURS = 40.0. The whole IF statement, taken from reference.py and
    from the mutated source, leaves the same WS-OT-HOURS and WS-GROSS for
    every EMP-RATE 0.00 .. 999.99; everything after it reads only storage."""
    from cobol_equiv.harness.corpus import apply_mutant

    ref = load_reference(DIRS["payroll"])
    src = (DIRS["payroll"] / "reference.py").read_text(encoding="utf-8")
    start = src.index('    if e["EMP-HOURS"].value > 40:')
    block = src[start:src.index('    gross = ws["WS-GROSS"].value', start)]
    s_ref = statement(block)
    s_mut = statement(apply_mutant(block, mutant("payroll", "overtime-ge-40")))
    e, ws_a, ws_b = Storage("EMP-REC", ref.EMP_REC), ref.working_storage(), ref.working_storage()
    move(Decimal("40.0"), e["EMP-HOURS"])
    for c in range(100000):
        move(Decimal(c).scaleb(-2), e["EMP-RATE"])
        exec(s_ref, vars(ref), {"e": e, "ws": ws_a})  # noqa: S102
        exec(s_mut, vars(ref), {"e": e, "ws": ws_b})  # noqa: S102
        assert ws_a.area == ws_b.area, c


def test_payroll_bracket_lt_at_gross_1000():
    """The mutant differs only when WS-GROSS = 1000.00; every way the
    reference reaches that gross with a whole-cent rate below 40 hours, plus
    the overtime case, gives the same output."""
    ref, mut = modules("payroll", "bracket-lt")
    cases = [("80.0", "10.00")]
    for tenths in range(1, 400):  # hours 0.1 .. 39.9
        c = Decimal(1000) / (Decimal(tenths).scaleb(-1))
        if c == c.quantize(Decimal("0.01")) and c < 1000:
            cases.append((str(Decimal(tenths).scaleb(-1)), str(c)))
    cases.append(("40.0", "25.00"))
    a, b = Payroll(ref), Payroll(mut)
    for hours, rate in cases:
        out, gross = a(hours, rate)
        assert gross == 1000
        assert out == b(hours, rate)[0], (hours, rate)


def test_datecalc_division_mutants_all_years():
    """DATE-TO-NUM for every WS-YYYY 1601 .. 9999 (the range it can be
    called with, docs/mutants.md): same WS-DAYNUM, WS-Q and WS-Y value."""
    ref = load_reference(DIRS["datecalc"])
    muts = [load_mutated(DIRS["datecalc"], mutant("datecalc", mid))
            for mid in ("python-floor-division", "year-unsigned-ignored")]
    progs = [ref.Program()] + [m.Program() for m in muts]
    for yyyy in range(1601, 10000):
        seen = []
        for p in progs:
            move(yyyy, p.ws["WS-YYYY"])
            move(3, p.ws["WS-MM"])
            move(1, p.ws["WS-DD"])
            p.date_to_num()
            seen.append((p.v("WS-DAYNUM"), p.v("WS-Q"), p.v("WS-Y")))
        assert seen[1:] == [seen[0]] * 2, yyyy


def test_classify_float_compare_near_thresholds():
    """CU-BALANCE S9(7)V99 is only compared with 0, 1000, 10000, 50000 and
    -500. Every balance within 1.00 of a threshold, and the extremes, give
    the same classification for each customer type and lateness class."""
    ref, mut = modules("classify", "float-compare")
    balances = {Decimal("-9999999.99"), Decimal("9999999.99"), Decimal("-0.00")}
    for t in (0, 1000, 10000, 50000, -500):
        balances |= {Decimal(t * 100 + k).scaleb(-2) for k in range(-100, 101)}
    for bal in sorted(balances):
        for typ in ("B", "P"):
            for late in (0, 31, 61, 91):
                outs = []
                for module in (ref, mut):
                    c = Storage("CUST-REC", module.CUST_REC)
                    move("C001", c["CU-ID"])
                    move(typ, c["CU-TYPE"])
                    move(30, c["CU-AGE"])
                    move(bal, c["CU-BALANCE"])
                    move(late, c["CU-DAYS-LATE"])
                    ws, out = module.working_storage(), bytearray()
                    module.classify_one(c, ws, out)
                    outs.append((bytes(out), bytes(ws.area)))
                assert outs[0] == outs[1], (bal, typ, late)


def test_no_equivalence_is_disproved_by_the_committed_run():
    path = ROOT / "results" / "gnucobol-3.1.2" / "mutation.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert not [r for r in rows if r["equivalence"] == "disproved"]
    claimed = {(r["program"], r["mutant"]) for r in rows if r["equivalence"] == "claimed"}
    assert claimed == EQUIVALENT


@pytest.mark.oracle
def test_ctlbreak_float_total_is_not_equivalent():
    """101 records of 99999.99 in one branch: the branch total passes the
    PICTURE of WS-BRANCH-TOT and the mutant no longer matches GnuCOBOL."""
    from cobol_equiv.harness.check import import_hits, run_once
    from cobol_equiv.harness.cobol import BUILD_DIR, compile_program

    d = DIRS["ctlbreak"]
    spec = load_spec(d)
    exe = compile_program(spec.source, BUILD_DIR)
    inp = {spec.inputs[0].name: b"R1B019999999\n" * 101}
    ref = load_reference(d)
    assert run_once(spec, exe, ref.main, inp, import_hits(ref)) is None
    mod = load_mutated(d, mutant("ctlbreak", "float-total"))
    diff = run_once(spec, exe, mod.main, inp, import_hits(mod))
    assert diff is not None
