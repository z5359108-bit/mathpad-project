#!/usr/bin/env python3
"""Vigenère şifreleme aracı.

Kullanım:
    python vigenere_tool.py encode "Selam" --key anahtar
    python vigenere_tool.py decode "..." --key anahtar
    python vigenere_tool.py encode -f dosya.txt --key gizli

Not: Yalnızca A-Z, a-z harfleri şifrelenir; anahtar harfleri büyük/küçük
duyarsızdır, alfabe dışı karakterler olduğu gibi kalır.
"""
import argparse
import sys


def _key_stream(text: str, key: str, reverse: bool = False):
    normalized = [ord(c.upper()) - ord("A") for c in key if c.isalpha()]
    if not normalized:
        raise ValueError("anahtar en az bir harf içermeli")
    index = 0
    for ch in text:
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            shift = normalized[index % len(normalized)]
            yield -shift if reverse else shift
            index += 1
        else:
            yield 0


def _transform(text: str, key: str, reverse: bool = False) -> str:
    out = []
    for ch, shift in zip(text, _key_stream(text, key, reverse)):
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            base = ord("A") if ch.isupper() else ord("a")
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


def encode(text: str, key: str) -> str:
    """Metni anahtarla Vigenère şifresiyle şifrele."""
    return _transform(text, key)


def decode(text: str, key: str) -> str:
    """Şifreli metni anahtarla çöz."""
    return _transform(text, key, reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vigenère şifreleme aracı")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("encode", "decode"):
        p = sub.add_parser(name, help="Metni şifrele/çöz")
        p.add_argument("text", nargs="?", help="İşlenecek metin")
        p.add_argument("-f", "--file", help="Metni bu dosyadan oku")
        p.add_argument("-k", "--key", required=True, help="Şifreleme anahtarı (harflerden oluşmalı)")

    args = parser.parse_args()
    func = encode if args.command == "encode" else decode

    try:
        data = args.text
        if args.file:
            with open(args.file, "r", encoding="utf-8") as fh:
                data = fh.read()
        if data is None:
            parser.error("ya metin ver ya da -f ile dosya belirt")
        print(func(data, args.key))
        return 0
    except (ValueError, OSError) as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
