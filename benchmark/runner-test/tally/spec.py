"""Runner test program (outside both benchmark tracks). Override: IN-CODE
from A, B (readable codes)."""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum, Num

HERE = Path(__file__).parent

RECORD = [Alnum("IN-CODE", "X"), Num("IN-AMT", "9(3)V99")]

SPEC = ProgramSpec(
    name="tally",
    area="runner test",
    source=HERE / "program.cob",
    inputs=[InputSpec("VALUES.DAT", RECORD, 0, 10, overrides={"IN-CODE": st.sampled_from(["A", "B"])})],
)
