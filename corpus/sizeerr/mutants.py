"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "float-divide",
        "category": "float",
        "description": "DIVIDE INTO the raw accumulator done in floating point and rounded with round()",
        "note": "differs on half-cent ties: Python round() rounds half to even (0.25 / 2.00 gives "
                "0.12, COBOL ROUNDED 0.13) and binary values just below a tie round down; whether the "
                "inputs contain such a pair depends on the sample",
        "edits": [(
            '        divide_into(amt, ws["WS-RAW"], rounded=True)\n',
            '        if amt.value != 0:\n'
            '            compute(ws["WS-RAW"], dec(repr(round(float(ws["WS-RAW"].value) / float(amt.value), 2))))\n',
        ), (
            'from cobol_equiv.runtime.files import LineSequentialReader\n',
            'from cobol_equiv.runtime.files import LineSequentialReader\n'
            'from cobol_equiv.runtime import compute, dec\n',
        )],
    },
    {
        "id": "multiply-not-rounded",
        "category": "rounding",
        "description": "MULTIPLY ... ROUNDED on the accumulator done without ROUNDED",
        "edits": [(
            'multiply(amt, ws["WS-ACC"], rounded=True, on_size_error=True)',
            'multiply(amt, ws["WS-ACC"], on_size_error=True)',
        )],
    },
    {
        "id": "size-error-stores",
        "category": "truncation",
        "description": "ADD with ON SIZE ERROR stores the truncated sum instead of leaving the target unchanged",
        "edits": [(
            'show(t, ws, out, add(amt, ws["WS-ACC"], on_size_error=True))',
            'show(t, ws, out, add(amt, ws["WS-ACC"]))',
        )],
    },
    {
        "id": "binary-no-truncation",
        "category": "truncation",
        "description": "WS-BIN declared COMP-5 (no truncation to PIC S9(4)) instead of COMP",
        "edits": [(
            'Num("WS-BIN", "S9(4)", usage=COMP, value=0)',
            'Num("WS-BIN", "S9(4)", usage="COMP-5", value=0)',
        )],
    },
    {
        "id": "subtract-sign",
        "category": "sign",
        "description": "SUBTRACT implemented as ADD on the raw accumulators",
        "edits": [(
            '        subtract(amt, [ws["WS-RAW"], ws["WS-BIN"]])',
            '        add(amt, [ws["WS-RAW"], ws["WS-BIN"]])',
        )],
    },
    {
        "id": "remainder-from-rounded-quotient",
        "category": "rounding",
        "description": "DIVIDE ... GIVING ... REMAINDER with ROUNDED quotient (remainder then changes)",
        "edits": [(
            'divide_remainder(ws["WS-ACC"], amt, ws["WS-QUOT"], ws["WS-REM"], on_size_error=True)',
            'divide_remainder(ws["WS-ACC"], amt, ws["WS-QUOT"], ws["WS-REM"], rounded=True, on_size_error=True)',
        )],
    },
    {
        "id": "count-after-dispatch",
        "category": "off-by-one",
        "description": "error counter not incremented for the first error",
        "note": "differs only when the first record of a file takes the size-error branch (that is, "
                "a D or Q record with amount 0, since the accumulator starts at 0); the fixed vectors "
                "have none and whether the generated inputs contain one depends on the sample",
        "edits": [(
            '    if error:\n        add(1, ws["WS-ERRORS"])',
            '    if error and ws["WS-COUNT"].value > 1:\n        add(1, ws["WS-ERRORS"])',
        )],
    },
    {
        "id": "ok-error-swapped",
        "category": "branch",
        "description": "ON SIZE ERROR and NOT ON SIZE ERROR branches swapped for SUBTRACT",
        "edits": [(
            'show(t, ws, out, subtract(amt, ws["WS-ACC"], on_size_error=True))',
            'show(t, ws, out, not subtract(amt, ws["WS-ACC"], on_size_error=True))',
        )],
    },
]
