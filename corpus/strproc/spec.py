"""Track R program (corpus/strproc), written for this repository.

Override and its reason: LN-TEXT from the characters the program's
UNSTRING, INSPECT and STRING statements act on (A-E, 0, space, comma), so
that delimiters and replaced characters occur often; narrows the PICTURE;
not stated by the program. This override predates the benchmark protocol
and is kept unchanged.
"""

from pathlib import Path

from hypothesis import strategies as st

from cobol_equiv.harness.compare import columns
from cobol_equiv.harness.spec import STDOUT, InputSpec, OutputLayout, ProgramSpec
from cobol_equiv.runtime import Alnum

HERE = Path(__file__).parent

OUT = columns(("WS-COMMAS", 2), ("FILLER", 1), ("WS-LEAD-SPACES", 2), ("FILLER", 1), ("WS-AS", 2),
              ("FILLER", 1), ("WS-NF", 2), ("FILLER", 1), ("WS-PTR", 2), ("FILLER", 1),
              ("WS-UOVF", 1), ("FILLER", 2), ("WS-F1", 8), ("FILLER", 2), ("WS-D1", 1),
              ("FILLER", 1), ("WS-C1", 2), ("FILLER", 1), ("WS-F2", 8), ("FILLER", 1),
              ("WS-C2", 2), ("FILLER", 1), ("WS-F3", 6), ("FILLER", 3), ("WS-OUT", 16),
              ("FILLER", 2), ("WS-OPTR", 2), ("FILLER", 1), ("WS-SOVF", 1))

SPEC = ProgramSpec(
    name="strproc",
    area="STRING / UNSTRING / INSPECT",
    source=HERE / "program.cob",
    inputs=[InputSpec("LINES.DAT", [Alnum("LN-TEXT", "X(30)")], 0, 10, overrides={
        "LN-TEXT": st.text(alphabet="ABCDE0 ,", max_size=30),
    })],
    layouts={STDOUT: OutputLayout(lambda line: OUT)},
    vectors=[
        {"LINES.DAT": b""},
        {"LINES.DAT": b"ALPHA,BETA GAMMA\n"
                      b"   AA00A,,B   C\n"
                      b"0000AAAA,BBBBBBBBBB,CCCCCCCCCC,DDD\n"
                      b",,,\n"
                      b"\n"
                      b"ABCDEABCDEABCDEABCDEABCDEABCDE\n"},
    ],
)
