"""Rosetta Code task "Decision tables", solution decision-tables.cob
(downloaded, not committed). Free format.

Three ACCEPTs of one character each. Override (domain stated by the
program's prompts "(Y or N)"): Y or N. Three lines per input. No fixed
vectors.

The Y/N domain has 8 inputs, so VISIBLE and DEV use all of them and
HELD-OUT holds only the boundary vectors (inputs outside Y/N). The program
also accepts lower-case y and n (FUNCTION UPPER-CASE); the override leaves
them out.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-decision-tables",
    area="EVALUATE ... ALSO, ACCEPT, FUNCTION UPPER-CASE on a group",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec(STDIN, [Alnum("ANSWER", "X")], 3, 3, overrides={
        "ANSWER": st.sampled_from(["Y", "N"]),
    })],
)
