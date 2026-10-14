def main(stdin: bytes, input_files: dict[str, bytes]) -> tuple[bytes, dict[str, bytes]]:
    data = input_files.get('unixdict.txt', b'')
    out = []

    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()

    def before(word: bytes, ch: int) -> int:
        idx = word.find(bytes([ch]))
        return len(word) if idx < 0 else idx

    for line in lines:
        word = line[:32].ljust(32, b' ')
        a = before(word, ord('a'))
        b = before(word, ord('b'))
        c = before(word, ord('c'))
        x = before(word, ord(' '))
        if a < b and b < c and c < x:
            out.append(word + b'\n')

    return b''.join(out), {}
