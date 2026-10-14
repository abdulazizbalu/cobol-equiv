"""Rosetta Code task "SEDOLs", solution sedols.cob (downloaded, not
committed). Free format.

Input sedol.txt, lines X(6). Override (domain stated by the task: 6-character
SEDOLs, digits and consonants): six characters from 0-9 and the uppercase
consonants. Fixed vector: the input list given in the task statement
(task.txt).
"""

import re
from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

_CHARS = "0123456789BCDFGHJKLMNPQRSTVWXYZ"


def _task_list() -> bytes:
    text = (HERE / "task.txt").read_text(encoding="utf-8")
    body = re.search(r"given this input:\n<pre>\n(.*?)</pre>", text, re.S).group(1)
    return body.encode("ascii")


SPEC = ProgramSpec(
    name="rc-sedols",
    area="reference modification, class tests, FUNCTION ORD / NUMVAL / MOD, EXIT PERFORM CYCLE",
    source=HERE / "program.cob",
    free_format=True,
    inputs=[InputSpec("sedol.txt", [Alnum("SEDOL", "X(6)")], 0, 12, overrides={
        "SEDOL": st.text(alphabet=_CHARS, min_size=6, max_size=6),
    })],
    vectors=[{"sedol.txt": _task_list()}],
)
