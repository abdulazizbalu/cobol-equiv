from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.harness.strategies import numeric_values
from cobol_equiv.runtime import Alnum, Num, Storage, move

HERE = Path(__file__).parent

# The generator fills the record by type, so the layout given to the harness
# is just the type code and the raw body.
RECORD = [Alnum("IR-TYPE", "X"), Alnum("IR-BODY", "X(29)")]
TEXT = st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", max_size=20)


def _body(items, draw_values):
    return st.fixed_dictionaries(draw_values).map(lambda vals: _build(items, vals))


def _build(items, vals):
    stg = Storage("BODY", items)
    for name, v in vals.items():
        move(v, stg[name])
    return bytes(stg.area)


HEADER = [Alnum("IH-NAME", "X(20)"), Num("IH-YYYY", "9(4)"), Num("IH-MM", "99"), Num("IH-DD", "99"),
          Alnum("F", "X")]
DETAIL = [Alnum("ID-ITEM", "X(5)"), Num("ID-QTY", "S9(4)"), Num("ID-PRICE", "9(5)V99"),
          Num("ID-DISC", "V99"), Alnum("F", "X(11)")]
TRAILER = [Alnum("IT-COUNT-X", "X(5)"), Num("IT-TOTAL", "S9(9)V99"), Alnum("F", "X(13)")]

header = _body(HEADER, {
    "IH-NAME": TEXT,
    "IH-YYYY": st.integers(0, 9999),
    "IH-MM": st.one_of(st.sampled_from([0, 1, 2, 12, 13]), st.integers(0, 99)),
    "IH-DD": st.one_of(st.sampled_from([0, 1, 28, 29, 30, 31, 32]), st.integers(0, 99)),
}).map(lambda b: b"H" + b)
detail = _body(DETAIL, {
    "ID-ITEM": st.text(alphabet="ABCXYZ0123456789", min_size=5, max_size=5),
    "ID-QTY": numeric_values(DETAIL[1]),
    "ID-PRICE": numeric_values(DETAIL[2]),
    "ID-DISC": numeric_values(DETAIL[3]),
}).map(lambda b: b"D" + b)
trailer = _body(TRAILER, {
    "IT-COUNT-X": st.integers(0, 3).map(lambda n: f"{n:05d}"),
    "IT-TOTAL": numeric_values(TRAILER[1]),
}).map(lambda b: b"T" + b)
other = st.sampled_from([b"X" + b" " * 29, b" " + b"0" * 29])


def rec(kind, **values):
    items = {"H": HEADER, "D": DETAIL, "T": TRAILER}[kind]
    from decimal import Decimal
    return (kind.encode() + _build(items, {k: Decimal(v) if isinstance(v, str) and k != "IH-NAME"
                                           and k != "ID-ITEM" and k != "IT-COUNT-X" else v
                                           for k, v in values.items()})).rstrip(b" ") + b"\n"


SPEC = ProgramSpec(
    name="redef",
    area="REDEFINES and variant records",
    source=HERE / "program.cob",
    inputs=[InputSpec("RECS.DAT", RECORD, 0, 15,
                      record_strategy=st.one_of(header, detail, detail, trailer, other))],
    layouts={STDOUT: OutputLayout(lambda line: None)},
    vectors=[
        {"RECS.DAT": b""},
        {"RECS.DAT": rec("H", **{"IH-NAME": "JANUARY RUN", "IH-YYYY": 2026, "IH-MM": 1, "IH-DD": 31})
                     + rec("H", **{"IH-NAME": "BAD MONTH", "IH-YYYY": 2026, "IH-MM": 13, "IH-DD": 1})
                     + rec("H", **{"IH-NAME": "FEB 29", "IH-YYYY": 2025, "IH-MM": 2, "IH-DD": 29})
                     + rec("D", **{"ID-ITEM": "AB001", "ID-QTY": "-3", "ID-PRICE": "19.99", "ID-DISC": "0.15"})
                     + rec("D", **{"ID-ITEM": "AB002", "ID-QTY": "2", "ID-PRICE": "0.05", "ID-DISC": "0.50"})
                     + rec("T", **{"IT-COUNT-X": "00002", "IT-TOTAL": "-50.92"})
                     + rec("D", **{"ID-ITEM": "AB003", "ID-QTY": "9999", "ID-PRICE": "99999.99", "ID-DISC": "0"})
                     + rec("T", **{"IT-COUNT-X": "00001", "IT-TOTAL": "0"})
                     + b"Q\n"},
    ],
)
