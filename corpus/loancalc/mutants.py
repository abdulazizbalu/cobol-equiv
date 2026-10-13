"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "float-payment",
        "category": "float",
        "description": "payment formula evaluated in binary floating point",
        "note": "not detected: a double keeps about 16 significant digits; the payment is rounded to cents "
                "(at most 9 digits), so the float result differs only when the exact value is within about "
                "1e-7 of a half-cent tie; no vector or generated input hit such a case",
        "edits": [(
            '        f = dec(ws["WS-FACTOR"])\n'
            '        if compute(ws["WS-PAYMENT"], dec(ln["LN-PRINCIPAL"]) * dec(ws["WS-MRATE"]) * f / (f - 1),',
            '        f = float(ws["WS-FACTOR"].value)\n'
            '        if compute(ws["WS-PAYMENT"], dec(repr(float(ln["LN-PRINCIPAL"].value)'
            ' * float(ws["WS-MRATE"].value) * f / (f - 1))),',
        )],
    },
    {
        "id": "interest-truncated",
        "category": "rounding",
        "description": "monthly interest truncated instead of ROUNDED",
        "edits": [(
            'compute(ws["WS-INTEREST"], dec(ws["WS-BALANCE"]) * dec(ws["WS-MRATE"]), rounded=True)',
            'compute(ws["WS-INTEREST"], dec(ws["WS-BALANCE"]) * dec(ws["WS-MRATE"]))',
        )],
    },
    {
        "id": "mrate-half-even",
        "equivalent": True,
        "category": "rounding",
        "description": "monthly rate rounded half-even (Python Decimal default) instead of half away from zero",
        "note": "equivalent mutant for this input domain: RATE/1200 with RATE in thousandths never has a "
                "tie at the 9th decimal place, so both rounding modes agree",
        "edits": [
            ('from cobol_equiv.runtime.files import LineSequentialReader\n',
             'from cobol_equiv.runtime.files import LineSequentialReader\n'
             'from decimal import ROUND_HALF_EVEN, Decimal\n'),
            ('compute(ws["WS-MRATE"], dec(ln["LN-RATE"]) / 1200, rounded=True)',
             'move((ln["LN-RATE"].value / 1200).quantize(Decimal("1E-8"), rounding=ROUND_HALF_EVEN), '
             'ws["WS-MRATE"])'),
        ],
    },
    {
        "id": "factor-no-size-error",
        "category": "truncation",
        "description": "ON SIZE ERROR on the growth factor ignored; truncated factor used",
        "edits": [(
            '            if compute(ws["WS-FACTOR"], dec(ws["WS-FACTOR"]) * (1 + dec(ws["WS-MRATE"])),\n'
            '                       rounded=True, on_size_error=True):',
            '            if compute(ws["WS-FACTOR"], dec(ws["WS-FACTOR"]) * (1 + dec(ws["WS-MRATE"])),\n'
            '                       rounded=True) and False:',
        )],
    },
    {
        "id": "residual-abs",
        "equivalent": True,
        "category": "sign",
        "description": "residual balance edited from its absolute value",
        "edits": [(
            'move(ws["WS-BALANCE"], ws["OL-RESIDUAL"])',
            'move(abs(ws["WS-BALANCE"].value), ws["OL-RESIDUAL"])',
        )],
        "note": "equivalent mutant: the balance can never become negative (the principal part is capped at the balance)",
    },
    {
        "id": "factor-loop-short",
        "category": "off-by-one",
        "description": "PERFORM LN-TERM TIMES runs one time less",
        "edits": [(
            'for _ in range(int(ln["LN-TERM"].value)):',
            'for _ in range(int(ln["LN-TERM"].value) - 1):',
        )],
    },
    {
        "id": "loop-limit-gt",
        "equivalent": True,
        "category": "off-by-one",
        "description": "amortisation loop stops on MONTH > TERM instead of >=",
        "note": "equivalent mutant: in the month equal to TERM the whole balance is paid, so the loop "
                "already ends on BALANCE <= 0",
        "edits": [(
            'ws["WS-MONTH"].value >= ln["LN-TERM"].value)',
            'ws["WS-MONTH"].value > ln["LN-TERM"].value)',
        )],
    },
    {
        "id": "zero-rate-branch-swapped",
        "category": "branch",
        "description": "IF WS-MRATE = 0 branches swapped",
        "edits": [(
            'if ws["WS-MRATE"].value == 0:',
            'if ws["WS-MRATE"].value != 0:',
        )],
    },
]
