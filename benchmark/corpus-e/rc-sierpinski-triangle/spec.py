"""Rosetta Code task "Sierpinski triangle", solution sierpinski-triangle.cob
(downloaded, not committed). Free format.

Adapted (adaptation.json): the task's input, the order N, hardcoded as
`move 4 to n`, is read with `accept n`. Override (domain stated by the task:
an order N; the item is PIC 99): decimal text of 0 .. 99. No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-sierpinski-triangle",
    area="nested PERFORM VARYING, COMPUTE with division into 9(18), DISPLAY WITH NO ADVANCING",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("N", "X(2)")], 1, 1, overrides={
        "N": st.integers(0, 99).map(str),
    })],
)
