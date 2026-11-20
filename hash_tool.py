#!/usr/bin/env python3
"""Hash (özet) hesaplama aracı.

Desteklenen algoritmalar: md5, sha1, sha224, sha256, sha384, sha512,
sha3_224, sha3_256, sha3_384, sha3_512, blake2b, blake2s

Kullanım:
    python hash_tool.py sha256 "Selam"
    python hash_tool.py sha512 -f dosya.bin
    python hash_tool.py all "Selam"          # tüm algoritmalar
"""
import argparse
import hashlib
import sys

ALGORITHMS = sorted(hashlib.algorithms_available & {
    "md5", "sha1", "sha224", "sha256", "sha384", "sha512",
    "sha3_224", "sha3_256", "sha3_384", "sha3_512", "blake2b", "blake2s",
})


def digest(data: bytes, algorithm: str) -> str:
    """Verilen baytların özetini hesapla."""
    try:
        return hashlib.new(algorithm, data).hexdigest()
    except ValueError:
        raise ValueError(f"desteklenmeyen algoritma: {algorithm}") from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash hesaplama aracı")
    parser.add_argument("algorithm", help=f"Algoritma adı ('all' = hepsi): {', '.join(ALGORITHMS)}")
    parser.add_argument("text", nargs="?", help="Özeti hesaplanacak metin")
    parser.add_argument("-f", "--file", help="İçeriği bu dosyadan oku")
    args = parser.parse_args()

    try:
        if args.text is not None:
            data = args.text.encode("utf-8")
        elif args.file:
            with open(args.file, "rb") as fh:
                data = fh.read()
        else:
            parser.error("ya metin ver ya da -f ile dosya belirt")

        targets = ALGORITHMS if args.algorithm == "all" else [args.algorithm]
        for algo in targets:
            print(f"{algo}: {digest(data, algo)}")
        return 0
    except (ValueError, OSError) as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
