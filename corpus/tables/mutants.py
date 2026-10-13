"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "amount-float",
        "category": "float",
        "description": "line amount qty * price computed in floating point and truncated with int()",
        "edits": [(
            '        compute(ws.f("WS-AMT", n), dec(it["IT-QTY"]) * dec(it["IT-PRICE"]))',
            '        compute(ws.f("WS-AMT", n), dec(int(float(it["IT-QTY"].value)'
            ' * float(it["IT-PRICE"].value) * 100)) / 100)',
        )],
    },
    {
        "id": "amount-no-truncation",
        "category": "truncation",
        "description": "accumulated amount capped at the maximum instead of truncated on the left",
        "edits": [(
            '            compute(ws.f("WS-AMT", tx), dec(ws.f("WS-AMT", tx)) + dec(it["IT-QTY"]) * dec(it["IT-PRICE"]))',
            '            total = ws.f("WS-AMT", tx).value + it["IT-QTY"].value * it["IT-PRICE"].value\n'
            '            move(min(total, type(total)("999999.99")), ws.f("WS-AMT", tx))',
        )],
    },
    {
        "id": "table-size-off-by-one",
        "category": "off-by-one",
        "description": "table accepts 7 entries instead of 8",
        "edits": [('    if ws["WS-COUNT"].value < SIZE:', '    if ws["WS-COUNT"].value < SIZE - 1:')],
    },
    {
        "id": "sort-unstable",
        "category": "branch",
        "description": "bubble sort swaps on <= (equal amounts change order)",
        "edits": [('if ws.f("WS-AMT", j).value < ws.f("WS-AMT", j + 1).value:',
                   'if ws.f("WS-AMT", j).value <= ws.f("WS-AMT", j + 1).value:')],
    },
    {
        "id": "search-from-two",
        "category": "off-by-one",
        "description": "SEARCH starts at the second entry",
        "edits": [('    for tx in range(1, SIZE + 1):', '    for tx in range(2, SIZE + 1):')],
    },
    {
        "id": "rank-sign",
        "equivalent": True,
        "category": "sign",
        "description": "quantity edited from a negated value",
        "edits": [('        move(ws.f("WS-QTY", i), ws["WL-QTY"])',
                   '        move(-ws.f("WS-QTY", i).value, ws["WL-QTY"])')],
        "note": "equivalent mutant: WL-QTY (ZZ,ZZ9) has no sign position, so the edited result is the same",
    },
]
