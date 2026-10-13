"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "detail-not-rounded",
        "category": "rounding",
        "description": "line amount truncated instead of ROUNDED",
        "edits": [('    compute(ws["WS-LINE-AMT"], dec(r["ID-QTY"]) * dec(r["ID-PRICE"]) * (1 - dec(r["ID-DISC"])),\n'
                   '            rounded=True)',
                   '    compute(ws["WS-LINE-AMT"], dec(r["ID-QTY"]) * dec(r["ID-PRICE"]) * (1 - dec(r["ID-DISC"])))')],
    },
    {
        "id": "qty-unsigned",
        "category": "sign",
        "description": "ID-QTY declared unsigned (overpunched negative quantities misread)",
        "edits": [('Num("ID-QTY", "S9(4)")', 'Num("ID-QTY", "9(4)")')],
    },
    {
        "id": "date-month-off-by-one",
        "category": "off-by-one",
        "description": "days-in-month table indexed with MM - 1",
        "edits": [('ws.f("WS-DAYS", int(mm)).value', 'ws.f("WS-DAYS", max(1, int(mm) - 1)).value')],
    },
    {
        "id": "redefines-shifted",
        "category": "truncation",
        "description": "IH-DATE-R laid out over the name instead of the date (wrong REDEFINES target)",
        "edits": [('              redefines="IH-DATE"),', '              redefines="IH-NAME"),')],
    },
    {
        "id": "trailer-or",
        "category": "branch",
        "description": "trailer check accepts a match on count OR total",
        "edits": [('            and r["IT-TOTAL"].value == ws["WS-RUN-TOTAL"].value):',
                   '            or r["IT-TOTAL"].value == ws["WS-RUN-TOTAL"].value):')],
    },
    {
        "id": "float-discount",
        "category": "float",
        "description": "discount factor computed in floating point",
        "note": "differs only when the line amount lands on a half-cent tie that the float factor "
                "moves; whether the generated inputs contain one depends on the sample",
        "edits": [('* (1 - dec(r["ID-DISC"]))', '* dec(repr(1 - float(r["ID-DISC"].value)))')],
    },
]
