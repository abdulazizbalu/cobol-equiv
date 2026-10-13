"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "format-instead-of-edit",
        "equivalent": True,
        "category": "float",
        "description": "L1-A built with a Python format string from a float instead of COBOL editing",
        "note": "equivalent on this input domain: for two-decimal values below 10**7 the float formats "
                "exactly, and keeping the last 11 characters drops the same high-order digits that "
                "COBOL truncates, with commas in the same positions",
        "edits": [(
            '        write_from("LINE-1")\n',
            '        v = float(a["AM-VALUE"].value)\n'
            '        ws["L1-A"].set_raw(f"{abs(v):>10,.2f}{\'-\' if v < 0 else \' \'}"[-11:].encode())\n'
            '        write_from("LINE-1")\n',
        )],
    },
    {
        "id": "cr-for-positive",
        "category": "sign",
        "description": "L1-B edited from the negated value (CR shown for positive amounts)",
        "edits": [('        move(a["AM-VALUE"], ws["L1-A"], ws["L1-B"], ws["L1-C"], ws["L2-G"], ws["L2-I"], ws["L2-J"])',
                   '        move(a["AM-VALUE"], ws["L1-A"], ws["L1-C"], ws["L2-G"], ws["L2-I"], ws["L2-J"])\n'
                   '        move(-a["AM-VALUE"].value, ws["L1-B"])')],
    },
    {
        "id": "qty-unsigned",
        "category": "sign",
        "description": "quantity total accumulated from absolute values",
        "edits": [('        add(a["AM-QTY"], ws["WS-QTY-TOTAL"])', '        add(abs(a["AM-QTY"].value), ws["WS-QTY-TOTAL"])')],
    },
    {
        "id": "wide-picture",
        "category": "truncation",
        "description": "L1-F declared one digit wider (----,--9), so large quantities are not truncated",
        "edits": [('Edited("L1-F", "---,--9")', 'Edited("L1-F", "----,--9")')],
    },
    {
        "id": "total-picture-short",
        "category": "truncation",
        "description": "TL-AMOUNT declared with one integer digit less (high-order digit lost)",
        "edits": [('Edited("TL-AMOUNT", "$$$$,$$$,$$9.99CR")', 'Edited("TL-AMOUNT", "$$$,$$$,$$$9.99CR")')],
    },
    {
        "id": "rounded-edit",
        "category": "rounding",
        "description": "L2-J (one decimal) rounded instead of truncated",
        "edits": [('        move(a["AM-QTY"], ws["L1-D"], ws["L1-F"], ws["L2-K"])',
                   '        compute(ws["L2-J"], dec(a["AM-VALUE"]), rounded=True)\n'
                   '        move(a["AM-QTY"], ws["L1-D"], ws["L1-F"], ws["L2-K"])'),
                  ('from cobol_equiv.runtime.files import', 'from cobol_equiv.runtime import compute, dec\n'
                   'from cobol_equiv.runtime.files import')],
    },
]
