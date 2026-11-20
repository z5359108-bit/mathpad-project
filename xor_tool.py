#!/usr/bin/env python3
"""XOR şifreleme aracı.

Kullanım:
    python xor_tool.py encode "Selam" --key sifre
    python xor_tool.py decode "0e0b2b19" --key sifre
    python xor_tool.py encode -f dosya.txt --key sifre

Not: Eğitim amaçlıdır, gerçek güvenlik için kullanılmamalıdır.
Şifreli çıktı unicode güvenliği için onaltılık (hex) metin olarak verilir.
"""
import argparse
import sys


def _xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode("utf-8")
    if not key_bytes:
        raise ValueError("anahtar boş olamaz")
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))


def encode(text: str, key: str) -> str:
    """Metni anahtarla XOR'layıp onaltılık metin döndür."""
    return _xor_bytes(text.encode("utf-8"), key).hex()


def decode(text: str, key: str) -> str:
    """Onaltılık metni anahtarla XOR'layıp çöz."""
    try:
        raw = bytes.fromhex("".join(text.split()))
    except ValueError:
        raise ValueError("girdi geçerli bir onaltılık metin değil") from None
    return _xor_bytes(raw, key).decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="XOR şifreleme aracı")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("encode", "decode"):
        p = sub.add_parser(name, help="Metni şifrele/çöz")
        p.add_argument("text", nargs="?", help="İşlenecek metin")
        p.add_argument("-f", "--file", help="Metni bu dosyadan oku")
        p.add_argument("-k", "--key", required=True, help="XOR anahtarı")

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
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
