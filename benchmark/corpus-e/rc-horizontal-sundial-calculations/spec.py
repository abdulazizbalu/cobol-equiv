"""Rosetta Code task "Horizontal sundial calculations", solution
horizontal-sundial-calculations.cob (downloaded, not committed). Free format.

Three ACCEPTs (latitude, longitude, legal meridian) into S9(3)V9(5) COMP.
Override (domain stated by the task: angles in degrees): decimal text of
-180 .. 180 with up to five decimals. Three lines per input. No fixed
vectors (the task's example is in degrees and minutes, not in the
program's input format).
"""

from decimal import Decimal
from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-horizontal-sundial-calculations",
    area="COMPUTE with FUNCTION SIN / TAN / ATAN / PI into COMP, ROUNDED, edited output",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("ANGLE", "X(10)")], 3, 3, overrides={
        "ANGLE": st.decimals(Decimal(-180), Decimal(180), places=5).map(lambda d: format(d.normalize(), "f")),
    })],
)
