"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "leap-no-century-rule",
        "category": "branch",
        "description": "leap year = divisible by 4 only",
        "edits": [('leap = self.v("WS-R4") == 0 and (self.v("WS-R100") != 0 or self.v("WS-R400") == 0)',
                   'leap = self.v("WS-R4") == 0')],
    },
    {
        "id": "range-gt-ge",
        "category": "off-by-one",
        "description": "upper range check uses >= MAX instead of > MAX",
        "note": "not detected: differs only when FROM + OFFSET lands exactly on 9999-12-31; no vector "
                "has it and random inputs are unlikely to hit one day out of three million",
        "edits": [('self.v("WS-NEW-NUM") > MAX_DAYNUM:', 'self.v("WS-NEW-NUM") >= MAX_DAYNUM:')],
    },
    {
        "id": "dow-index-zero-based",
        "category": "off-by-one",
        "description": "day-of-week table indexed with the remainder (0-based) clamped to 1",
        "edits": [('compute(ws["WS-DOW-IX"], dec(ws["WS-REM7"]) + 1)',
                   'compute(ws["WS-DOW-IX"], dec(ws["WS-REM7"]) + (0 if self.v("WS-REM7") else 1))')],
    },
    {
        "id": "python-floor-division",
        "equivalent": True,
        "category": "rounding",
        "description": "years/4 computed with Python floor division on a signed value instead of DIVIDE",
        "edits": [('        divide_giving(ws["WS-Y"], 4, ws["WS-Q"])',
                   '        move(int(dec(ws["WS-YYYY"]).to_decimal() - 1601) // 4, ws["WS-Q"])')],
        "note": "equivalent mutant: WS-YYYY is at least 1601 whenever DATE-TO-NUM runs, so the "
                "dividend is never negative and floor and truncating division agree",
    },
    {
        "id": "diff-abs",
        "category": "sign",
        "description": "date difference shown without its sign",
        "edits": [('compute(ws["WS-DIFF"], dec(ws["WS-TO-NUM"]) - dec(ws["WS-FROM-NUM"]))',
                   'compute(ws["WS-DIFF"], abs(ws["WS-TO-NUM"].value - ws["WS-FROM-NUM"].value))')],
    },
    {
        "id": "year-unsigned-ignored",
        "equivalent": True,
        "category": "sign",
        "description": "WS-Y declared signed (S9(5)) although the program relies on 9(5)",
        "edits": [('Num("WS-Y", "9(5)")', 'Num("WS-Y", "S9(5)")')],
        "note": "equivalent mutant: WS-YYYY - 1601 is never negative on any path, so the sign of "
                "WS-Y never matters",
    },
    {
        "id": "float-estimate",
        "category": "float",
        "description": "year estimate computed as round(n / 365.2425) in floating point",
        "edits": [('        divide_giving(ws["WS-DAYNUM"], 366, ws["WS-Y"])',
                   '        move(int(round(float(self.v("WS-DAYNUM")) / 365.2425)), ws["WS-Y"])')],
    },
]
