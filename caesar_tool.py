#!/usr/bin/env python3
"""Caesar şifreleme aracı.

Kullanım:
    python caesar_tool.py encode "Selam" --shift 3
    python caesar_tool.py decode "Vhodp" --shift 3
    python caesar_tool.py encode "Merhaba"            # varsayılan shift=13 (ROT13)
    python caesar_tool.py encode -f dosya.txt --shift 5

Not: Yalnızca A-Z, a-z harfleri kaydırılır; diğer karakterler olduğu gibi kalır.
"""
import argparse
import sys

A_UPPER = range(ord("A"), ord("Z") + 1)
A_LOWER = range(ord("a"), ord("z") + 1)


def _shift_char(ch: str, shift: int) -> str:
    code = ord(ch)
    if code in A_UPPER:
        base = ord("A")
    elif code in A_LOWER:
        base = ord("a")
    else:
        return ch
    return chr((code - base + shift) % 26 + base)


def _shift_text(text: str, shift: int) -> str:
    return "".join(_shift_char(c, shift) for c in text)


def encode(text: str, shift: int = 13) -> str:
    """Metni verilen kaydırmayla şifrele."""
    return _shift_text(text, shift)


def decode(text: str, shift: int = 13) -> str:
    """Şifreli metni çözmek için ters kaydır."""
    return _shift_text(text, -shift)


def main() -> int:
    parser = argparse.ArgumentParser(description="Caesar şifreleme aracı")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func in (("encode", "şifrele"), ("decode", "çöz")):
        p = sub.add_parser(name, help=f"Metni {func}")
        p.add_argument("text", nargs="?", help="İşlenecek metin")
        p.add_argument("-f", "--file", help="Metni bu dosyadan oku")
        p.add_argument("-s", "--shift", type=int, default=13, help="Kaydırma miktarı (varsayılan: 13)")

    args = parser.parse_args()
    func = encode if args.command == "encode" else decode

    try:
        data = args.text
        if args.file:
            with open(args.file, "r", encoding="utf-8") as fh:
                data = fh.read()
        if data is None:
            parser.error("ya metin ver ya da -f ile dosya belirt")
        print(func(data, args.shift))
        return 0
    except OSError as exc:
        print(f"Hata: dosya okunamadı ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
