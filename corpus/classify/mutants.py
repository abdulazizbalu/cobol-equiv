"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "evaluate-order",
        "category": "branch",
        "description": "EVALUATE TRUE: DEFAULT tested before CREDIT (first true WHEN changes)",
        "edits": [('    if bal < 0:\n        move("CREDIT", ws["WS-CLASS"]); add(1, ws["WS-CNT-CREDIT"])\n'
                   '    elif late > 90:\n        move("DEFAULT", ws["WS-CLASS"]); add(1, ws["WS-CNT-DEFAULT"])\n',
                   '    if late > 90:\n        move("DEFAULT", ws["WS-CLASS"]); add(1, ws["WS-CNT-DEFAULT"])\n'
                   '    elif bal < 0:\n        move("CREDIT", ws["WS-CLASS"]); add(1, ws["WS-CNT-CREDIT"])\n')],
    },
    {
        "id": "and-or",
        "category": "branch",
        "description": "WATCH condition uses OR instead of AND",
        "edits": [('    elif late > 30 and bal > 1000:', '    elif late > 30 or bal > 1000:')],
    },
    {
        "id": "thru-exclusive",
        "category": "off-by-one",
        "description": "\"G\" THRU \"J\" treated as exclusive of J",
        "edits": [('    elif b"G" <= typ <= b"J":', '    elif b"G" <= typ < b"J":')],
    },
    {
        "id": "age-boundary",
        "category": "off-by-one",
        "description": "CU-AGE < 25 written as <= 25",
        "edits": [('    if typ == b"P" and age < 25:', '    if typ == b"P" and age <= 25:')],
    },
    {
        "id": "balance-unsigned",
        "category": "sign",
        "description": "balance compared as an absolute value",
        "edits": [('    bal = c["CU-BALANCE"].value', '    bal = abs(c["CU-BALANCE"].value)')],
    },
    {
        "id": "not-dropped",
        "category": "branch",
        "description": "NOT CU-BALANCE < 0 written without NOT",
        "edits": [('    elif late == 0 and not bal < 0:', '    elif late == 0 and bal < 0:')],
    },
    {
        "id": "float-compare",
        "equivalent": True,
        "category": "float",
        "description": "balance thresholds compared on float values",
        "edits": [('    bal = c["CU-BALANCE"].value', '    bal = float(c["CU-BALANCE"].value)')],
        "note": "equivalent mutant: the balance is only compared with 0, 1000, 10000, 50000 and "
                "-500; its float differs from it by less than 1.2e-9 while a balance differs from a "
                "threshold by 0.01 or more, so every comparison keeps its result (docs/mutants.md)",
    },
]
