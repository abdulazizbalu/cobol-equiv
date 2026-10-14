"""Rosetta Code task "Abbreviations, automatic", solution
abbreviations-automatic.cob (downloaded, not committed).

Input file days-of-week.txt: lines of up to 200 characters. Override
(domain stated by the task): a line is either empty or seven day names
separated by single spaces; a name is 1-14 printable non-space ASCII
characters. Fixed vector: the list given in the task statement (task.txt).
"""

import re
from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

_name = st.text(alphabet=[chr(c) for c in range(0x21, 0x7F)], min_size=1, max_size=14)
_line = st.one_of(st.just(""), st.lists(_name, min_size=7, max_size=7).map(" ".join))


def _task_list() -> bytes:
    text = (HERE / "task.txt").read_text(encoding="utf-8")
    body = re.search(r'<pre style="height:45ex">\n(.*?)</pre>', text, re.S).group(1)
    return body.encode("utf-8")


SPEC = ProgramSpec(
    name="rc-abbreviations-automatic",
    area="UNSTRING with POINTER, INSPECT TALLYING, reference modification",
    source=HERE / "program.cob",
    inputs=[InputSpec("days-of-week.txt", [Alnum("DOW-LINE", "X(200)")], 0, 12,
                      overrides={"DOW-LINE": _line})],
    vectors=[{"days-of-week.txt": _task_list()}],
)
