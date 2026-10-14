def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get('unixdict.txt', b'')
    out = bytearray()
    recs = data.split(b'\n')
    if recs and recs[-1] == b'':
        recs.pop()
    for line in recs:
        word = line[:32].ljust(32, b' ')

        def before(ch):
            i = word.find(ch)
            return 32 if i < 0 else i

        a = before(b'a')
        b = before(b'b')
        c = before(b'c')
        x = before(b' ')
        if a < b and b < c and c < x:
            out += word + b'\n'
    return bytes(out), {}
