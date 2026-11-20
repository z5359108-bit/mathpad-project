#!/usr/bin/env python3
"""Base64 encode/decode aracı.

Kullanım:
    python base64_tool.py encode "Selam Dünya"
    python base64_tool.py decode "U2VsYW0gRMO8bnlh"
    python base64_tool.py encode -f dosya.txt
"""
import argparse
import base64
import sys


def encode(text: str) -> str:
    """Metni base64'e çevir."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode(text: str) -> str:
    """base64'ü UTF-8 metne çöz."""
    return base64.b64decode(text.encode("ascii"), validate=True).decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Base64 encode/decode aracı")
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Metni base64'e çevir")
    enc.add_argument("text", nargs="?", help="Kodlanacak metin")
    enc.add_argument("-f", "--file", help="Metni bu dosyadan oku")

    dec = sub.add_parser("decode", help="base64'ü metne çevir")
    dec.add_argument("text", nargs="?", help="Çözülecek base64 metni")
    dec.add_argument("-f", "--file", help="base64 girdisini bu dosyadan oku")

    args = parser.parse_args()

    try:
        data = args.text
        if args.file:
            with open(args.file, "r", encoding="utf-8") as fh:
                data = fh.read()
        if data is None:
            parser.error("ya metin ver ya da -f ile dosya belirt")
        print(encode(data) if args.command == "encode" else decode(data))
        return 0
    except (UnicodeDecodeError, ValueError) as exc:
        print(f"Hata: geçersiz girdi ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
