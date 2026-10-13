"""Emitting fixed-format COBOL source for oracle programs."""

from __future__ import annotations

from decimal import Decimal

from ..runtime.storage import Item

AREA_A = " " * 7
AREA_B = " " * 11
MAX_COL = 72


def num_literal(d: Decimal | int) -> str:
    d = Decimal(d)
    s = format(d, "f")
    if s.startswith("-0") and d == 0:
        s = s[1:]
    return s


def alnum_literal(b: bytes) -> str:
    s = b.decode("latin-1")
    if '"' in s:
        raise ValueError("quote in literal not supported by generator")
    return f'"{s}"'


def wrap(tokens: list[str], indent: str = AREA_B, cont: str = AREA_B + "  ") -> list[str]:
    """Join tokens into lines that end before column 73."""
    lines: list[str] = []
    cur = indent
    for t in tokens:
        cand = (cur + " " + t) if cur.strip() else (cur + t)
        if len(cand) > MAX_COL and cur.strip():
            lines.append(cur)
            cur = cont + t
        else:
            cur = cand
        if len(cur) > MAX_COL:
            raise ValueError(f"token too long for one line: {t!r}")
    if cur.strip():
        lines.append(cur)
    return lines


def stmt(text: str) -> list[str]:
    """Wrap a statement, keeping quoted literals as single tokens."""
    tokens: list[str] = []
    buf = ""
    in_q = False
    for ch in text:
        if ch == '"':
            in_q = not in_q
            buf += ch
        elif ch == " " and not in_q:
            if buf:
                tokens.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return wrap(tokens)


def data_decl(item: Item, level: int = 5, wrap_group: bool = True) -> list[str]:
    """01 G-<name>. 05 <name> PIC ... so that DISPLAY G-<name> shows raw bytes."""
    out = []
    if wrap_group:
        out.append(f"{AREA_A}01 G-{item.name}.")
    out += _decl(item, level)
    return out


def _decl(item: Item, level: int) -> list[str]:
    pad = AREA_A + " " * (level // 5 * 2)
    words = [f"{level:02d}", item.name]
    if item.redefines:
        words += ["REDEFINES", item.redefines]
    if item.pic is not None:
        words += ["PIC", item.pic.text]
        if item.usage != "DISPLAY":
            words += [item.usage]
    if item.occurs:
        words += ["OCCURS", str(item.occurs)]
    if item.value is not None:
        v = item.value
        words += ["VALUE", alnum_literal(v.encode("latin-1")) if isinstance(v, str) else num_literal(v)]
    lines = wrap(words, indent=pad, cont=pad + "    ")
    lines[-1] += "."
    for c in item.children:
        lines += _decl(c, level + 5)
    return lines


def program(name: str, data: list[str], proc: list[str]) -> str:
    head = [
        f"{AREA_A}IDENTIFICATION DIVISION.",
        f"{AREA_A}PROGRAM-ID. {name}.",
        f"{AREA_A}DATA DIVISION.",
        f"{AREA_A}WORKING-STORAGE SECTION.",
        f"{AREA_A}01 SE-FLAG PIC X.",
        f"{AREA_A}01 LEN-OUT PIC 9(6).",
    ]
    body = [f"{AREA_A}PROCEDURE DIVISION."] + proc
    return "\n".join(head + data + body) + "\n"
