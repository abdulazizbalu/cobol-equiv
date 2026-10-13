"""Deliberately wrong variants of reference.py, for measuring the harness."""

MUTANTS = [
    {
        "id": "no-final-break",
        "category": "off-by-one",
        "description": "last branch and region totals not written at end of file",
        "edits": [('        else:\n            self.branch_break()\n            self.region_break()\n',
                   '        else:\n            pass\n')],
    },
    {
        "id": "region-before-branch",
        "category": "branch",
        "description": "on a region change the region total is written before the branch total",
        "edits": [('            self.branch_break()\n            self.region_break()\n        elif',
                   '            self.region_break()\n            self.branch_break()\n        elif')],
    },
    {
        "id": "branch-check-only",
        "category": "branch",
        "description": "region change not checked; only branch changes trigger a break",
        "edits": [('        elif sl["SL-REGION"].raw != ws["WS-PREV-REGION"].raw:\n'
                   '            self.branch_break()\n            self.region_break()\n',
                   '')],
    },
    {
        "id": "abs-amounts",
        "category": "sign",
        "description": "negative sales added as positive",
        "edits": [('        add(sl["SL-AMOUNT"], ws["WS-BRANCH-TOT"])',
                   '        add(abs(sl["SL-AMOUNT"].value), ws["WS-BRANCH-TOT"])')],
    },
    {
        "id": "float-total",
        "category": "float",
        "description": "branch total accumulated in a Python float and moved at the break",
        "edits": [('        add(sl["SL-AMOUNT"], ws["WS-BRANCH-TOT"])',
                   '        self.ftot = getattr(self, "ftot", 0.0) + float(sl["SL-AMOUNT"].value)\n'
                   '        move(dec(f"{self.ftot:.2f}"), ws["WS-BRANCH-TOT"])'),
                  ('    def branch_break(self):\n        ws = self.ws\n',
                   '    def branch_break(self):\n        ws = self.ws\n        self.ftot = 0.0\n'),
                  ('from cobol_equiv.runtime.files import', 'from cobol_equiv.runtime import dec\n'
                   'from cobol_equiv.runtime.files import')],
        "note": "not equivalent: once a branch total passes 9,999,999.99 (101 records of 99999.99 "
                "in one branch) COBOL truncates the total while the mutant's MOVE of the float sum is "
                "refused by the runtime; generated and boundary files have at most 30 records, so no "
                "branch total gets there. Classified as equivalent before; see docs/mutants.md",
    },
    {
        "id": "trailing-spaces-kept",
        "category": "truncation",
        "description": "report lines written with their trailing spaces (LINE SEQUENTIAL WRITE does not keep them)",
        "edits": [('        self.writer.write(self.rpt["REPORT-LINE"])\n\n    def run',
                   '        self.writer._buf += self.rpt["REPORT-LINE"].raw + b"\\n"\n\n    def run')],
    },
]
