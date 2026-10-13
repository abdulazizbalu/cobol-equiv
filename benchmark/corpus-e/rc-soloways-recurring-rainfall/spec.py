"""Rosetta Code task "Soloway's recurring rainfall", solution
soloways-recurring-rainfall.cob (downloaded, not committed).

ACCEPTs integers into 9(9) until 99999. Override and finalize (domain
stated by the task: integers, and input stops with the value 99999):
decimal text of 0 .. 999999999, and every input ends with a line 99999.
No fixed vectors.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import STDIN, InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum, Storage, move

HERE = Path(__file__).parent

LINE = [Alnum("CURRENT", "X(9)")]


def _terminate(records: list) -> list:
    end = Storage(STDIN, LINE)
    move("99999", end["CURRENT"])
    return records + [end]


SPEC = ProgramSpec(
    name="rc-soloways-recurring-rainfall",
    area="ACCEPT loop with GO TO, running average with COMPUTE division",
    source=HERE / "program.cob",
    inputs=[InputSpec(STDIN, LINE, 0, 12, finalize=_terminate, overrides={
        "CURRENT": st.integers(0, 999999999).map(str),
    })],
)
