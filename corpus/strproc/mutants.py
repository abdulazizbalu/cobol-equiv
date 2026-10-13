"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "unstring-all-dropped",
        "category": "branch",
        "description": "DELIMITED BY ALL \" \" treated as a single-space delimiter",
        "edits": [('[",", (" ", True)]', '[",", " "]')],
    },
    {
        "id": "leading-as-all",
        "category": "branch",
        "description": "TALLYING FOR LEADING \" \" counts all spaces",
        "edits": [('Phrase("LEADING", " ", counter=f("WS-LEAD-SPACES"))',
                   'Phrase("ALL", " ", counter=f("WS-LEAD-SPACES"))')],
    },
    {
        "id": "before-initial-dropped",
        "category": "off-by-one",
        "description": "BEFORE INITIAL \",\" ignored when counting A",
        "edits": [('Phrase("ALL", "A", counter=f("WS-AS"), before=",")',
                   'Phrase("ALL", "A", counter=f("WS-AS"))')],
    },
    {
        "id": "pointer-not-reset",
        "category": "off-by-one",
        "description": "STRING pointer starts at 2 instead of 1",
        "edits": [('    move(1, f("WS-OPTR"))', '    move(2, f("WS-OPTR"))')],
    },
    {
        "id": "string-pads",
        "category": "truncation",
        "description": "STRING result built in Python and space-padded/truncated, overflow never flagged",
        "edits": [(
            '    if string([(f("WS-F2"), SPACES), ("/", None), (f("WS-F1"), " "), ("/", None), (f("WS-F3"), None)],\n'
            '              f("WS-OUT"), pointer=f("WS-OPTR")):\n'
            '        move("Y", f("WS-SOVF"))',
            '    s = (f("WS-F2").raw.split(b" ")[0] + b"/" + f("WS-F1").raw.split(b" ")[0] + b"/"\n'
            '         + f("WS-F3").raw)\n'
            '    move(s, f("WS-OUT"))\n'
            '    move(min(len(s), 16) + 1, f("WS-OPTR"))',
        )],
    },
    {
        "id": "python-replace-first",
        "category": "branch",
        "description": "REPLACING LEADING \"0\" done with str.replace (replaces every 0)",
        "edits": [(
            '    inspect_replacing(f("WS-F1"), [Phrase("ALL", "A", by="4"), Phrase("LEADING", "0", by="*")])',
            '    move(f("WS-F1").raw.replace(b"A", b"4").replace(b"0", b"*"), f("WS-F1"))',
        )],
    },
]
