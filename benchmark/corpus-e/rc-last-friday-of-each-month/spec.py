"""Rosetta Code task "Last Friday of each month", solution
last-friday-of-each-month.cob (downloaded, not committed).

One ACCEPT into 9999. Override (domain stated by the task, "a given year",
and by the program's own validation, 1601 thru 9999): decimal text of
1601 .. 9999. No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-last-friday-of-each-month",
    area="FUNCTION INTEGER-OF-DATE / DATE-OF-INTEGER / MOD, REDEFINES of a date group, BINARY group",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("YR", "X(4)")], 1, 1, overrides={
        "YR": st.integers(1601, 9999).map(str),
    })],
)
