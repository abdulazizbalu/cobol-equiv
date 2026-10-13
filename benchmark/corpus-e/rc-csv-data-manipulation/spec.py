"""Rosetta Code task "CSV data manipulation", solution
csv-data-manipulation.cob (downloaded, not committed).

Input csv.txt, lines X(64); output new.csv.txt. Override (domain stated by
the task: CSV data whose fields contain no commas; the task's file has five
numeric columns): five comma-separated unsigned integers of 1-5 digits.
Fixed vector: the CSV file given in the task statement (task.txt).
"""

import re
from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.spec import InputSpec, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

_num = st.integers(0, 99999).map(str)
_line = st.lists(_num, min_size=5, max_size=5).map(",".join)


def _task_file() -> bytes:
    text = (HERE / "task.txt").read_text(encoding="utf-8")
    m = re.search(r"For this task we will use the following CSV file:\n\n((?: .*\n)+)", text)
    return "".join(line[1:] + "\n" for line in m.group(1).splitlines()).encode("ascii")


SPEC = ProgramSpec(
    name="rc-csv-data-manipulation",
    area="UNSTRING into numeric items, STRING with TRIM, edited sum",
    source=HERE / "program.cob",
    inputs=[InputSpec("csv.txt", [Alnum("CSV-RECORD", "X(64)")], 0, 10,
                      overrides={"CSV-RECORD": _line})],
    outputs=["new.csv.txt"],
    vectors=[{"csv.txt": _task_file()}],
)
