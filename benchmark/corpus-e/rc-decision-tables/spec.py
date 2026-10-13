"""Rosetta Code task "Decision tables", solution decision-tables.cob
(downloaded, not committed). Free format.

Three ACCEPTs of one character each. Override (domain stated by the
program's prompts "(Y or N)"): Y or N. Three lines per input. No fixed
vectors.
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
