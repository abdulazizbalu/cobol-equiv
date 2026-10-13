"""Rosetta Code task "Julia set", solution julia-set.cob (downloaded, not
committed). Free format.

Two ACCEPTs (the real and imaginary parts of the constant) into S9V999.
No overrides: the task states no input domain, so lines are any printable
text of up to 6 characters. Two lines per input. No fixed vectors.
"""

from pathlib import Path

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-julia-set",
    area="fixed-point complex iteration with MULTIPLY / DIVIDE GIVING truncation",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("C-PART", "X(6)")], 2, 2)],
)
