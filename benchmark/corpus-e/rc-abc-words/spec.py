"""Rosetta Code task "ABC words", solution abc-words.cob (downloaded, not
committed).

Input file unixdict.txt (named by VALUE OF FILE-ID), one word per line,
record X(32). Override (domain stated by the task: the words of a
dictionary): 1-20 lowercase ASCII letters. No fixed vector (the task's
word list is an external file, not part of the task statement).
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

SPEC = ProgramSpec(
    name="rc-abc-words",
    area="INSPECT TALLYING BEFORE INITIAL, READ loop with GO TO",
    source=HERE / "program.cob",
    inputs=[InputSpec("unixdict.txt", [Alnum("WORD", "X(32)")], 0, 30, overrides={
        "WORD": st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
    })],
)
