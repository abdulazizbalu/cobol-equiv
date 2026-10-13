"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "float-gross",
        "category": "float",
        "description": "regular-hours gross computed in binary floating point",
        "note": "differs only when HOURS * RATE is a half-cent tie whose binary value lies below the tie "
                "(e.g. 0.1 hours at 0.35); whether the generated inputs contain one depends on the sample: "
                "a trial run with 150 inputs from the earlier input generator found one, the committed "
                "run did not",
        "edits": [(
            'compute(ws["WS-GROSS"], dec(e["EMP-HOURS"]) * dec(e["EMP-RATE"]), rounded=True)',
            'compute(ws["WS-GROSS"], dec(repr(float(e["EMP-HOURS"].value) * float(e["EMP-RATE"].value))),'
            ' rounded=True)',
        )],
    },
    {
        "id": "tax-truncated",
        "category": "rounding",
        "description": "middle tax bracket truncated instead of ROUNDED",
        "edits": [(
            'compute(ws["WS-TAX"], 100 + (dec(ws["WS-GROSS"]) - 1000) * dec("0.25"), rounded=True)',
            'compute(ws["WS-TAX"], 100 + (dec(ws["WS-GROSS"]) - 1000) * dec("0.25"))',
        )],
    },
    {
        "id": "adjust-abs",
        "category": "sign",
        "description": "signed adjustment read as its absolute value",
        "edits": [(
            '+ dec(e["EMP-ADJUST"]))',
            '+ dec(abs(e["EMP-ADJUST"].value)))',
        )],
    },
    {
        "id": "packed-gross-unsigned",
        "category": "sign",
        "description": "PAY-GROSS declared unsigned COMP-3 (sign nibble F instead of C)",
        "edits": [(
            'Num("PAY-GROSS", "S9(7)V99", usage=COMP3)',
            'Num("PAY-GROSS", "9(7)V99", usage=COMP3)',
        )],
    },
    {
        "id": "overtime-ge-40",
        "equivalent": True,
        "category": "off-by-one",
        "description": "overtime from 40 hours inclusive (>= instead of >)",
        "edits": [(
            'if e["EMP-HOURS"].value > 40:',
            'if e["EMP-HOURS"].value >= 40:',
        )],
        "note": "equivalent mutant: at exactly 40.0 hours the overtime part is 0, so both branches give the same gross",
    },
    {
        "id": "bracket-lt",
        "equivalent": True,
        "category": "off-by-one",
        "description": "first tax bracket uses < 1000 instead of <= 1000",
        "edits": [(
            'if gross <= 1000:',
            'if gross < 1000:',
        )],
        "note": "equivalent mutant: at gross 1000.00 both brackets give tax 100.00",
    },
    {
        "id": "dedcode-swapped",
        "category": "branch",
        "description": "deduction codes A and B swapped",
        "edits": [(
            'if code == b"A":',
            'if code == b"B":',
        ), (
            'elif code == b"B":',
            'elif code == b"A":',
        )],
    },
]
