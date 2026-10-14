"""Rosetta Code task "Increment a numerical string", solution
increment-a-numerical-string-2.cob (downloaded, not committed). The first
solution, increment-a-numerical-string-1.cob, failed E4 (see screening.csv).

Adapted (adaptation.json): the numerical string, hardcoded as VALUE 12345,
is read with ACCEPT num-str. Override (domain stated by the task: a
numerical string; the item is PIC 9(5)): decimal text of 0 .. 99999. No
fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-increment-a-numerical-string",
    area="ACCEPT into 9(5), ADD 1 with high-order truncation",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, [Alnum("NUM-STR", "X(5)")], 1, 1, overrides={
        "NUM-STR": st.integers(0, 99999).map(str),
    })],
)
