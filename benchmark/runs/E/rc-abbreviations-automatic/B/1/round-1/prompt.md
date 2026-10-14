Translate the COBOL program below into a Python module.

The module must behave exactly like the program compiled with GnuCOBOL 3.1.2
(cobc -x -std=default): for every input whose records fit the program's
record descriptions, it must produce byte for byte the same standard output
and output files.

Use the Python package cobol_equiv.runtime, documented in the API reference
below, for COBOL data and statements. Besides it, use only the Python
standard library.

## IO contract
The Python module must define

    def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]

- stdin: everything the program reads with ACCEPT (one ACCEPT reads one line).
- input_files: for every file the program reads, the name in its ASSIGN
  clause mapped to the full content of the file. LINE SEQUENTIAL files are
  lines that end with "\n"; SEQUENTIAL files are fixed-length records
  without separators.
- The return value is all bytes the program writes to standard output, and
  a dict that maps the ASSIGN name of every file the program opens for
  output to the full content of that file.
- The module must not read the clock, random sources, the network or the
  file system, and must not start processes. It runs on Python 3.12.

## Examples
These are inputs and the exact outputs of the COBOL program.
### Example 1
stdin = b''
input_files = {'days-of-week.txt': b'\n'}
expected stdout = b' \n'
expected output_files = {}

### Example 2
stdin = b''
input_files = {'days-of-week.txt': b'0 0 0 0 0 0 0\n'}
expected stdout = b'Line 001: Error: identical days\n'
expected output_files = {}

## API reference: cobol_equiv.runtime
# API reference: cobol_equiv.runtime

`cobol_equiv.runtime` models COBOL data items and statements in Python.
Data is described with Storage, Group, Num, Alnum, Edited and Filler;
every item is a FieldRef at a fixed offset of one bytearray, so REDEFINES,
group moves and record I/O work on the actual bytes. Statements are
functions. Numeric operands may be FieldRefs, ints, Decimals, numeric
strings ("0.05") or CobDecimal values from dec(). A function raises
Unsupported, MoveError or PicError for a case outside the modelled subset.

```python
from cobol_equiv.runtime import Storage, Group, Num, Alnum, Edited, COMP3, move, add, compute, dec
ws = Storage("WS", [
    Num("AMOUNT", "S9(5)V99", usage=COMP3, value="0"),
    Group("IN-DATE", [Num("YYYY", "9(4)"), Num("MM", "99"), Num("DD", "99")]),
    Num("IN-DATE-N", "9(8)", redefines="IN-DATE"),
    Group("ENTRY", [Alnum("CODE", "X(3)"), Num("QTY", "9(3)")], occurs=10),
])
ws["AMOUNT"]       # FieldRef
ws.f("QTY", 3)     # QTY (3); subscripts are 1-based, outermost first
compute(ws["AMOUNT"], dec(ws.f("QTY", 3)) * dec("1.5"), rounded=True)
```

### Storage(name: str, items: list[Item], area: bytearray | None = None)

A record or WORKING-STORAGE area. `items`: list of Item from Num, Alnum, Edited, Filler, Group. Without `area` the storage is initialised as COBOL does (VALUE clauses applied). `st[name]` returns the FieldRef of a data name (first occurrence); `st.f(name, *subs)` the FieldRef of a subscripted item; `st.record()` the whole area as one FieldRef (for READ ... INTO it). Data names must be unique within one Storage.

### Group(name, children, occurs=None, redefines=None) -> Item

Group item. `children`: list of Item. `occurs`: OCCURS n. `redefines`: name of an earlier sibling.

### Num(name, pic, usage='DISPLAY', value=None, occurs=None, redefines=None) -> Item

Numeric item, e.g. Num("BAL", "S9(5)V99", usage=COMP3, value="0"). usage: DISPLAY (default), COMP, COMP3, COMP5. value: VALUE clause (number, numeric string or figurative constant).

### Alnum(name, pic, value=None, occurs=None, redefines=None) -> Item

Alphanumeric (PIC X) or alphabetic (PIC A) item.

### Edited(name, pic, value=None, occurs=None, redefines=None) -> Item

Numeric-edited item, e.g. Edited("OUT", "ZZ,ZZ9.99-").

### Filler(pic, value=None) -> Item

Unnamed item (FILLER), e.g. Filler("X(3)", " - ").

### FieldRef

One item at a position in a storage area. Properties: `raw` (bytes), `text` (str, latin-1), `value` (Decimal, numeric items only), `pic`, `usage`, `category`. `set_raw(bytes)` replaces the bytes (same length). `int(ref)` gives the integer value.

### refmod(f: FieldRef, start: int, length: int | None = None) -> FieldRef

Reference modification: refmod(ref, start, length) is `ref (start:length)`, refmod(ref, start) is `ref (start:)`. The result is an alphanumeric FieldRef sharing the item's storage, usable as sender or receiver.

### move(src, *dsts: FieldRef) -> None

MOVE src TO each of dsts. src: a FieldRef, an alphanumeric literal (str or bytes), a numeric literal (int or Decimal) or a figurative constant (SPACES, ZEROS, HIGH_VALUES, LOW_VALUES, All("x")).

### initialize(f: FieldRef) -> None

INITIALIZE f (no REPLACING phrase).

### add(operands, targets, *, rounded=False, on_size_error=False) -> bool

ADD operands TO targets. operands: one operand or a list. targets: a FieldRef, (FieldRef, rounded) or a list of these. Returns True if a size error occurred; pass on_size_error=True when the statement has ON SIZE ERROR or NOT ON SIZE ERROR.

### add_giving(operands, giving, *, rounded=False, on_size_error=False) -> bool

ADD operands GIVING giving; ADD a TO b GIVING c is add_giving([a, b], c).

### subtract(operands, targets, *, rounded=False, on_size_error=False) -> bool

SUBTRACT operands FROM targets. Arguments and result as for add.

### subtract_giving(operands, minuend, giving, *, rounded=False, on_size_error=False) -> bool

SUBTRACT operands FROM minuend GIVING giving.

### multiply(operand, targets, *, rounded=False, on_size_error=False) -> bool

MULTIPLY operand BY targets.

### multiply_giving(a, b, giving, *, rounded=False, on_size_error=False) -> bool

MULTIPLY a BY b GIVING giving.

### divide_into(divisor, targets, *, rounded=False, on_size_error=False) -> bool

DIVIDE divisor INTO targets.

### divide_giving(dividend, divisor, giving, *, rounded=False, on_size_error=False) -> bool

DIVIDE dividend BY divisor GIVING giving (also DIVIDE divisor INTO dividend GIVING giving).

### divide_remainder(dividend, divisor, quotient: FieldRef, remainder: FieldRef, *, rounded=False, on_size_error=False) -> bool

DIVIDE dividend BY divisor GIVING quotient REMAINDER remainder.

### compute(targets, value, *, rounded=False, on_size_error=False) -> bool

COMPUTE targets = value. value is an expression of CobDecimal values, e.g. compute(x, dec(a) * dec(b) / 100 - dec(c), rounded=True); +, -, *, / and unary minus are available, written in the COBOL order of evaluation.

### dec(x) -> CobDecimal

CobDecimal from a FieldRef, int, Decimal or numeric string, for compute expressions and comparisons.

### CobDecimal

Intermediate result of compute expressions. `to_decimal()` gives a Decimal.

### display_line(*items) -> bytes

The bytes DISPLAY item ... writes, newline included. Items: FieldRefs and literals (str or bytes; a numeric literal is passed as its text, e.g. "12").

### display_bytes(item) -> bytes

The bytes DISPLAY writes for one item, without newline.

### string(parts, into: FieldRef, pointer: FieldRef | None = None) -> bool

STRING ... INTO into [WITH POINTER pointer]. parts: list of (source, delimiter); delimiter None means DELIMITED BY SIZE. Returns True on overflow.

### unstring(source, delimiters, targets, pointer: FieldRef | None = None, tallying: FieldRef | None = None) -> bool

UNSTRING source [DELIMITED BY ...] INTO targets [WITH POINTER pointer] [TALLYING IN tallying]. delimiters: list of str, bytes or FieldRef, or (delimiter, True) for ALL delimiter; an empty list means no DELIMITED BY. targets: FieldRef or Into. Returns True on overflow.

### Into(field: FieldRef, delimiter_in: FieldRef | None = None, count_in: FieldRef | None = None) -> None

One UNSTRING receiver with optional DELIMITER IN and COUNT IN items.

### Phrase(mode: str, pattern: object = None, by: object = None, counter: FieldRef | None = None, before: object = None, after: object = None) -> None

One INSPECT phrase. mode: "ALL", "LEADING", "FIRST" (REPLACING only) or "CHARACTERS"; pattern: searched text; by: replacement (REPLACING); counter: FieldRef (TALLYING); before / after: INITIAL delimiters.

### inspect_tallying(field, phrases: list[Phrase]) -> None

INSPECT field TALLYING with a list of Phrase (each with counter).

### inspect_replacing(field: FieldRef, phrases: list[Phrase]) -> None

INSPECT field REPLACING with a list of Phrase (each with by).

### inspect_converting(field: FieldRef, from_chars, to_chars, before=None, after=None) -> None

INSPECT field CONVERTING from_chars TO to_chars [BEFORE|AFTER INITIAL x].

### Stdin(data: bytes)

Standard input for ACCEPT: inp = Stdin(stdin_bytes); inp.accept(ref) is ACCEPT ref.

### accept_line(line: bytes, ref: FieldRef) -> None

Store one input line (without newline) into ref as ACCEPT does.

### SPACES

Figurative constant SPACE / SPACES.

### ZEROS

Figurative constant ZERO / ZEROS / ZEROES.

### HIGH_VALUES

Figurative constant HIGH-VALUE / HIGH-VALUES.

### LOW_VALUES

Figurative constant LOW-VALUE / LOW-VALUES.

### All(lit: str | bytes)

ALL "literal" as a sender.

### DISPLAY

USAGE DISPLAY.

### COMP

USAGE COMP / BINARY.

### COMP3

USAGE COMP-3 / PACKED-DECIMAL.

### COMP5

USAGE COMP-5.

### Unsupported

Raised for a construct or data case outside the modelled subset.

### MoveError

Raised for a MOVE outside the modelled subset.

### PicError

Raised for a PICTURE outside the modelled subset.

### DataError

Raised when an item holds bytes that are not valid for its USAGE.

## cobol_equiv.runtime.files

### LineSequentialReader(data: bytes, record_size: int, long_lines: str = 'truncate')

LINE SEQUENTIAL input file: LineSequentialReader(data, record_size), record_size being the record length in bytes; leave long_lines at its default. read(into) reads the next record into the FieldRef `into` and returns its bytes, or returns None at end of file.

### LineSequentialWriter()

LINE SEQUENTIAL output file. write(record) with a FieldRef or bytes; getvalue() returns the file contents.

### RecordSequentialReader(data: bytes, record_size: int)

ORGANIZATION SEQUENTIAL (fixed-length records) input file; read as for LineSequentialReader.

### RecordSequentialWriter()

ORGANIZATION SEQUENTIAL output file; write and getvalue as for LineSequentialWriter.

## COBOL program
```cobol
            IDENTIFICATION DIVISION.
            PROGRAM-ID. AUTO-ABBREVIATIONS.

            ENVIRONMENT DIVISION.

            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
              SELECT DOW ASSIGN TO "days-of-week.txt"
              ORGANIZATION IS LINE SEQUENTIAL.

            DATA DIVISION.
              FILE SECTION.
              FD DOW.
              01 DOW-FILE PIC X(200).

              WORKING-STORAGE SECTION.
              01 DOW-LINE PIC X(200).
              01 ENDO PIC 9(1).
              01 ENDO2 PIC 9(1).
              01 CURDAY PIC X(50).
              01 ABPTR PIC 999.
              01 LINE-NUM PIC 9(3) VALUE 1.
              01 CHARAMT PIC 9(3) VALUE 1.
              01 LARGESTCHARAMT PIC 9(3).
              01 DAYNUM PIC 9(3) VALUE 1.
              01 ABRESTART PIC 9(1).
              01 CURABBR PIC X(50).
              01 TMP1 PIC 9(3).
              01 TMP2 PIC 9(3).
              01 TINDEX PIC 9(3) VALUE 1.
              01 ABBRLIST.
                05 ABBRITEM PIC X(50) OCCURS 7 TIMES.


            PROCEDURE DIVISION.
              OPEN INPUT DOW.
                PERFORM UNTIL ENDO = 1
                  READ DOW INTO DOW-LINE
                    AT END MOVE 1 TO ENDO
                    NOT AT END PERFORM
                      IF DOW-LINE = "" THEN
                        DISPLAY ""
                      ELSE
                        MOVE 0 TO ENDO2
                        MOVE 0 TO CHARAMT

                        PERFORM UNTIL ENDO2 > 0
                          MOVE 1 TO ABPTR
                          MOVE 1 TO DAYNUM
                          MOVE 0 TO ABRESTART

                          ADD 1 TO CHARAMT

                          MOVE 1 TO TINDEX
                          PERFORM 7 TIMES
                            MOVE SPACE TO ABBRITEM(TINDEX)
                            ADD 1 TO TINDEX
                          END-PERFORM

                          PERFORM 7 TIMES
                            UNSTRING DOW-LINE DELIMITED BY SPACE
                              INTO CURDAY
                              WITH POINTER ABPTR
                            END-UNSTRING

                            MOVE 0 TO TMP1
                            MOVE 0 TO TMP2
                            INSPECT CURDAY
                              TALLYING TMP1 FOR ALL CHARACTERS
                            INSPECT CURDAY
                              TALLYING TMP2 FOR ALL SPACE
                            SUBTRACT TMP2 FROM TMP1
                            IF TMP1 > LARGESTCHARAMT THEN
                              MOVE TMP1 TO LARGESTCHARAMT
                            END-IF

                            IF CURDAY = "" THEN
                              MOVE 3 TO ENDO2
                            END-IF

                            MOVE CURDAY(1:CHARAMT) TO CURABBR

                            MOVE 1 TO TINDEX
                            PERFORM 7 TIMES
                              IF ABBRITEM(TINDEX) = CURABBR THEN
                                MOVE 1 TO ABRESTART
                              END-IF
                              ADD 1 TO TINDEX
                            END-PERFORM

                            MOVE CURABBR TO ABBRITEM(DAYNUM)

                            ADD 1 TO DAYNUM

                          END-PERFORM

                          IF ABRESTART = 0 THEN
                            MOVE 1 TO ENDO2
                          END-IF

                          IF CHARAMT > LARGESTCHARAMT THEN
                            MOVE 2 TO ENDO2
                          END-IF

                        END-PERFORM

                        DISPLAY "Line " LINE-NUM ": " WITH NO ADVANCING

                        IF ENDO2 = 3 THEN
                          DISPLAY "Error: not enough " WITH NO ADVANCING
                          DISPLAY "days"
                        ELSE IF ENDO2 = 2 THEN
                          DISPLAY "Error: identical " WITH NO ADVANCING
                          DISPLAY "days"
                        ELSE
                          DISPLAY CHARAMT ": " WITH NO ADVANCING

                          MOVE 1 TO TINDEX
                          PERFORM 7 TIMES
                            MOVE ABBRITEM(TINDEX) TO CURABBR

                            MOVE 0 TO TMP1
                            MOVE 0 TO TMP2
                            INSPECT CURABBR
                              TALLYING TMP1 FOR ALL CHARACTERS
                            INSPECT CURABBR
                              TALLYING TMP2 FOR TRAILING SPACES
                            SUBTRACT TMP2 FROM TMP1

                            DISPLAY CURABBR(1:TMP1) WITH NO ADVANCING
                            DISPLAY "." WITH NO ADVANCING

                            IF TINDEX < 7 THEN
                              DISPLAY SPACE WITH NO ADVANCING
                            ELSE
                              DISPLAY X"0a" WITH NO ADVANCING
                            END-IF

                            ADD 1 TO TINDEX
                          END-PERFORM
                        END-IF

                      END-IF

                    END-PERFORM
                  END-READ

                  ADD 1 TO LINE-NUM
                END-PERFORM.
              CLOSE DOW.
              STOP RUN.
```

## Your previous translation
```python
from cobol_equiv.runtime import (
    Storage, Group, Num, Alnum, move, add, unstring, display_line, SPACES,
)
from cobol_equiv.runtime.files import LineSequentialReader


def main(stdin: bytes, input_files: dict) -> tuple:
    fd = Storage("FD", [Alnum("DOW-FILE", "X(200)")])
    ws = Storage("WS", [
        Alnum("DOW-LINE", "X(200)"),
        Num("ENDO", "9(1)"),
        Num("ENDO2", "9(1)"),
        Alnum("CURDAY", "X(50)"),
        Num("ABPTR", "999"),
        Num("LINE-NUM", "9(3)", value=1),
        Num("CHARAMT", "9(3)", value=1),
        Num("LARGESTCHARAMT", "9(3)"),
        Num("DAYNUM", "9(3)", value=1),
        Num("ABRESTART", "9(1)"),
        Alnum("CURABBR", "X(50)"),
        Num("TMP1", "9(3)"),
        Num("TMP2", "9(3)"),
        Num("TINDEX", "9(3)", value=1),
        Group("ABBRLIST", [Alnum("ABBRITEM", "X(50)", occurs=7)]),
    ])
    CURDAY_OFF = 202

    out = bytearray()
    reader = LineSequentialReader(input_files.get("days-of-week.txt", b""), 200)

    dow_line = ws["DOW-LINE"]
    curday = ws["CURDAY"]
    curabbr = ws["CURABBR"]

    while int(ws["ENDO"]) != 1:
        rec = reader.read(fd["DOW-FILE"])
        if rec is None:
            move(1, ws["ENDO"])
        else:
            move(fd["DOW-FILE"], dow_line)
            if dow_line.raw.strip(b" ") == b"":
                out += display_line("")
            else:
                move(0, ws["ENDO2"])
                move(0, ws["CHARAMT"])
                while int(ws["ENDO2"]) <= 0:
                    move(1, ws["ABPTR"])
                    move(1, ws["DAYNUM"])
                    move(0, ws["ABRESTART"])
                    add(1, ws["CHARAMT"])
                    for i in range(1, 8):
                        move(SPACES, ws.f("ABBRITEM", i))
                    move(8, ws["TINDEX"])
                    for _ in range(7):
                        unstring(dow_line, [" "], [curday], pointer=ws["ABPTR"])
                        raw = curday.raw
                        tmp1 = 50 - raw.count(b" ")
                        move(tmp1, ws["TMP1"])
                        move(raw.count(b" "), ws["TMP2"])
                        if int(ws["TMP1"]) > int(ws["LARGESTCHARAMT"]):
                            move(ws["TMP1"], ws["LARGESTCHARAMT"])
                        if raw.strip(b" ") == b"":
                            move(3, ws["ENDO2"])
                        n = int(ws["CHARAMT"])
                        area = ws.record().raw
                        piece = area[CURDAY_OFF:CURDAY_OFF + n]
                        if piece:
                            move(piece, curabbr)
                        else:
                            move(SPACES, curabbr)
                        ca = curabbr.raw
                        for i in range(1, 8):
                            if ws.f("ABBRITEM", i).raw == ca:
                                move(1, ws["ABRESTART"])
                        move(8, ws["TINDEX"])
                        dn = int(ws["DAYNUM"])
                        if 1 <= dn <= 7:
                            move(curabbr, ws.f("ABBRITEM", dn))
                        add(1, ws["DAYNUM"])
                    if int(ws["ABRESTART"]) == 0:
                        move(1, ws["ENDO2"])
                    if int(ws["CHARAMT"]) > int(ws["LARGESTCHARAMT"]):
                        move(2, ws["ENDO2"])

                out += display_line("Line ", ws["LINE-NUM"], ": ")[:-1]
                e2 = int(ws["ENDO2"])
                if e2 == 3:
                    out += b"Error: not enough "
                    out += b"days\n"
                elif e2 == 2:
                    out += b"Error: identical "
                    out += b"days\n"
                else:
                    out += display_line(ws["CHARAMT"], ": ")[:-1]
                    for t in range(1, 8):
                        move(ws.f("ABBRITEM", t), curabbr)
                        raw = curabbr.raw
                        trailing = len(raw) - len(raw.rstrip(b" "))
                        tmp1 = 50 - trailing
                        move(tmp1, ws["TMP1"])
                        move(trailing, ws["TMP2"])
                        if tmp1 > 0:
                            out += raw[:tmp1]
                        out += b"."
                        if t < 7:
                            out += b" "
                        else:
                            out += b"\n"
                    move(8, ws["TINDEX"])
        add(1, ws["LINE-NUM"])

    return bytes(out), {}
```

## Test result
The previous translation was run on a test input that is not one of the
examples above.
stdin = b''
input_files = {'days-of-week.txt': b"Sunday Monday Tuesday Wednesday Thursday Friday Saturday\nSondag Maandag Dinsdag Woensdag Donderdag Vrydag Saterdag\nE_djel\xc3\xab E_h\xc3\xabn\xc3\xab E_mart\xc3\xab E_m\xc3\xabrkur\xc3\xab E_enjte E_premte E_shtun\xc3\xab\nEhud Segno Maksegno Erob Hamus Arbe Kedame\nAl_Ahad Al_Ithinin Al_Tholatha'a Al_Arbia'a Al_Kamis Al_Gomia'a Al_Sabit\nGuiragui Yergou_shapti Yerek_shapti Tchorek_shapti Hink_shapti Ourpat Shapat\ndomingu llunes martes mi\xc3\xa9rcoles xueves vienres s\xc3\xa1badu\nBazar_g\xc3\x9cn\xc3\x9c Birinci_g\xc3\x9cn \xc3\x87kinci_g\xc3\x9cn \xc3\x9c\xc3\xa7\xc3\x9cnc\xc3\x9c_g\xc3\x9cn D\xc3\x96rd\xc3\x9cnc\xc3\x9c_g\xc3\x9cn Bes,inci_g\xc3\x9cn Alt\xc3\xb2nc\xc3\xb2_g\xc3\x9cn\nIgande Astelehen Astearte Asteazken Ostegun Ostiral Larunbat\nRobi_bar Shom_bar Mongal_bar Budhh_bar BRihashpati_bar Shukro_bar Shoni_bar\nNedjelja Ponedeljak Utorak Srijeda Cxetvrtak Petak Subota\nDisul Dilun Dimeurzh Dimerc'her Diriaou Digwener Disadorn\nnedelia ponedelnik vtornik sriada chetvartak petak sabota\nsing_kei_yaht sing_kei_yat sing_kei_yee sing_kei_saam sing_kei_sie sing_kei_ng sing_kei_luk\nDiumenge Dilluns Dimarts Dimecres Dijous Divendres Dissabte\nDzeenkk-eh Dzeehn_kk-ehreh Dzeehn_kk-ehreh_nah_kay_dzeeneh Tah_neesee_dzeehn_neh Deehn_ghee_dzee-neh Tl-oowey_tts-el_dehlee Dzeentt-ahzee\ndy_Sul dy_Lun dy_Meurth dy_Mergher dy_You dy_Gwener dy_Sadorn\nDimanch Lendi Madi M\xc3\xa8kredi Jedi Vandredi Samdi\nnedjelja ponedjeljak utorak srijeda cxetvrtak petak subota\nnede^le ponde^l\xc3\xad \xc3\xbater\xc3\xbf str^eda c^tvrtek p\xc3\xa1tek sobota\nSondee Mondee Tiisiday Walansedee TOOsedee Feraadee Satadee\ns0ndag mandag tirsdag onsdag torsdag fredag l0rdag\nzondag maandag dinsdag woensdag donderdag vrijdag zaterdag\nDiman^co Lundo Mardo Merkredo ^Ja\xc3\xb9do Vendredo Sabato\np\xc3\x9chap\xc3\xa4ev esmasp\xc3\xa4ev teisip\xc3\xa4ev kolmap\xc3\xa4ev neljap\xc3\xa4ev reede laup\xc3\xa4ev\n\nDiu_prima Diu_sequima Diu_tritima Diu_quartima Diu_quintima Diu_sextima Diu_sabbata\nsunnudagur m\xc3\xa1nadagur t\xc3\xbfsdaguy mikudagur h\xc3\xb3sdagur friggjadagur leygardagur\nYek_Sham'beh Do_Sham'beh Seh_Sham'beh Cha'har_Sham'beh Panj_Sham'beh Jom'eh Sham'beh\nsunnuntai maanantai tiistai keskiviiko torsktai perjantai lauantai\ndimanche lundi mardi mercredi jeudi vendredi samedi\nSnein Moandei Tiisdei Woansdei Tonersdei Freed Sneon\nDomingo Segunda_feira Martes M\xc3\xa9rcores Joves Venres S\xc3\xa1bado\nk'vira orshabati samshabati otkhshabati khutshabati p'arask'evi shabati\nSonntag Montag Dienstag Mittwoch Donnerstag Freitag Samstag\nKiriaki' Defte'ra Tri'ti Teta'rti Pe'mpti Paraskebi' Sa'bato\nravivaar somvaar mangalvaar budhvaar guruvaar shukravaar shanivaar\np\xc3\xb3pule p\xc3\xb3`akahi p\xc3\xb3`alua p\xc3\xb3`akolu p\xc3\xb3`ah\xc3\xa1 p\xc3\xb3`alima p\xc3\xb3`aono\nYom_rishon Yom_sheni Yom_shlishi Yom_revi'i Yom_chamishi Yom_shishi Shabat\nravivara somavar mangalavar budhavara brahaspativar shukravara shanivar\nvas\xc3\xa1rnap h\xc3\xa9tf\xc3\xb6 kedd szerda cs\xc3\xbct\xc3\xb6rt\xc3\xb6k p\xc3\xa9ntek szombat\nSunnudagur M\xc3\xa1nudagur \xe2\x95\x9eri\xce\xb4judagur Mi\xce\xb4vikudagar Fimmtudagur F\xc3\x96studagur Laugardagur\nsundio lundio mardio merkurdio jovdio venerdio saturdio\nMinggu Senin Selasa Rabu Kamis Jumat Sabtu\nDominica Lunedi Martedi Mercuridi Jovedi Venerdi Sabbato\nD\xc3\xa9_Domhnaigh D\xc3\xa9_Luain D\xc3\xa9_M\xc3\xa1irt D\xc3\xa9_Ceadaoin D\xc3\xa9_ardaoin D\xc3\xa9_hAoine D\xc3\xa9_Sathairn\ndomenica luned\xc3\xad marted\xc3\xad mercoled\xc3\xad gioved\xc3\xad venerd\xc3\xad sabato\nNichiyou_bi Getzuyou_bi Kayou_bi Suiyou_bi Mokuyou_bi Kin'you_bi Doyou_bi\nIl-yo-il Wol-yo-il Hwa-yo-il Su-yo-il Mok-yo-il Kum-yo-il To-yo-il\nDies_Dominica Dies_Lun\xc3\xa6 Dies_Martis Dies_Mercurii Dies_Iovis Dies_Veneris Dies_Saturni\nsve-tdien pirmdien otrdien tresvdien ceturtdien piektdien sestdien\nSekmadienis Pirmadienis Antradienis Trec^iadienis Ketvirtadienis Penktadienis S^es^tadienis\nWangu Kazooba Walumbe Mukasa K...(cut)}
First difference: <stdout> line 26, column 1: expected b' ', got b''

Fix the translation. Reply with the complete corrected Python module in one
```python code block. Do not write anything after the code block.
