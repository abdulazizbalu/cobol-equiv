"""Rosetta Code task "Leap year", solution leap-year-2.cob (downloaded, not
committed). The first solution, leap-year-1.cob, failed E3 (see
screening.csv).

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
    name="rc-leap-year",
    area="FUNCTION INTEGER-OF-DAY / DATE-OF-INTEGER / MOD, BINARY group",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("INPUT-YEAR", "X(4)")], 1, 1, overrides={
        "INPUT-YEAR": st.integers(1601, 9999).map(str),
    })],
)
