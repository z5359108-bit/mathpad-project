#!/usr/bin/env python3
"""Güvenli şifre üretici (rastgele, secrets tabanlı).

Kullanım:
    python password_gen_tool.py --length 20
    python password_gen_tool.py --length 32 --count 5
    python password_gen_tool.py --length 12 --no-symbols
    python password_gen_tool.py --length 8 --no-lower --no-upper
"""
import argparse
import secrets
import string
import sys


def generate(length: int = 16, *, lower: bool = True, upper: bool = True,
             digits: bool = True, symbols: bool = True) -> str:
    """Belirtilen karakter havuzundan kriptografik olarak güvenli şifre üret."""
    pool = ""
    if lower:
        pool += string.ascii_lowercase
    if upper:
        pool += string.ascii_uppercase
    if digits:
        pool += string.digits
    if symbols:
        pool += "!@#$%^&*()-_=+[]{};:,.?"
    if not pool:
        raise ValueError("en az bir karakter türü seçilmeli")
    if length < 1:
        raise ValueError("uzunluk en az 1 olmalı")
    return "".join(secrets.choice(pool) for _ in range(length))


def main() -> int:
    parser = argparse.ArgumentParser(description="Güvenli şifre üretici")
    parser.add_argument("-l", "--length", type=int, default=16, help="Şifre uzunluğu (varsayılan: 16)")
    parser.add_argument("-c", "--count", type=int, default=1, help="Üretilecek şifre sayısı (varsayılan: 1)")
    parser.add_argument("--no-lower", action="store_true", help="Küçük harfleri çıkar")
    parser.add_argument("--no-upper", action="store_true", help="Büyük harfleri çıkar")
    parser.add_argument("--no-digits", action="store_true", help="Rakamları çıkar")
    parser.add_argument("--no-symbols", action="store_true", help="Sembolleri çıkar")
    args = parser.parse_args()

    try:
        for _ in range(args.count):
            print(generate(
                args.length,
                lower=not args.no_lower,
                upper=not args.no_upper,
                digits=not args.no_digits,
                symbols=not args.no_symbols,
            ))
        return 0
    except ValueError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
