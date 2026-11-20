# zeyrox_projects

Kişisel Python araçları ve test ortamı. Tüm araçlar yalnızca standart kütüphaneyi (stdlib) kullanır, ek bağımlılık gerektirmez.

## Yapı

```
.
├── base64_tool.py            # Base64 encode/decode
├── caesar_tool.py            # Caesar şifresi (ROT13 dahil)
├── vigenere_tool.py          # Vigenère şifresi
├── xor_tool.py               # XOR şifresi (hex çıktı)
├── hash_tool.py              # md5/sha1/sha256/... özet hesaplama
├── password_gen_tool.py      # Güvenli rastgele şifre üretici
├── tests/                    # Her araç için birim testleri
└── .gitignore
```

## Kullanım

### Base64
```bash
python base64_tool.py encode "Selam Dünya"
python base64_tool.py decode "U2VsYW0gRMO8bnlh"
python base64_tool.py encode -f dosya.txt
```

### Caesar (varsayılan kaydırma 13 = ROT13)
```bash
python caesar_tool.py encode "Selam" --shift 3
python caesar_tool.py decode "Vhodp" --shift 3
```

### Vigenère
```bash
python vigenere_tool.py encode "Selam Dünya" --key anahtar
python vigenere_tool.py decode "..." --key anahtar
```

### XOR (hex çıktı)
```bash
python xor_tool.py encode "Selam" --key sifre
python xor_tool.py decode "..." --key sifre
```

### Hash
```bash
python hash_tool.py sha256 "Selam"
python hash_tool.py all "Selam"        # tüm algoritmalar
python hash_tool.py sha512 -f dosya.bin
```

### Şifre üretici
```bash
python password_gen_tool.py --length 20 --count 5
python password_gen_tool.py --length 12 --no-symbols
```

## Testler

```bash
python -m unittest discover -s tests -v
```
