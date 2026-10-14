"""Rosetta Code task "Formatted numeric output", solution
formatted-numeric-output.cob (downloaded, not committed). Free format.

Adapted (adaptation.json): the task's input number, hardcoded as
`MOVE 7.125 TO X`, is read with `ACCEPT X`. Override (domain stated by the
task: a decimal number, here for X PIC 9(5)V9(3)): decimal text of
0 .. 99999.999 with up to three decimals. No fixed vectors.
"""

from decimal import Decimal
from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-formatted-numeric-output",
    area="ACCEPT into a numeric item with decimals, DISPLAY of 9(5)V9(3)",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("X", "X(9)")], 1, 1, overrides={
        "X": st.decimals(Decimal(0), Decimal("99999.999"), places=3).map(lambda d: format(d.normalize(), "f")),
    })],
)
