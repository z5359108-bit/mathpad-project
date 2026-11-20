# zeyrox_projects

Kişisel Python araçları, şifreleme araçları ve **MathPad** matematik çözücü.

## MathPad — Modüler Akıllı Matematik Çözücü

Doğal dille yazılan matematik sorularını adım adım çözer, sonuçları **deftere
yazılabilir LaTeX formatında** verir (`$$...$$` blokları, MathJax uyumlu HTML defteri).

```bash
pip install -r requirements.txt        # yalnızca sympy

# Tek soru — çıktı her zaman deftere kopyalanabilir LaTeX'tir
python -m mathpad "integral of x^2 from 0 to 3"

# Etkileşimli REPL: her cevap LaTeX blokları ($$...$$) halinde gelir
python -m mathpad
python -m mathpad --notebook defter.md --html defter.html

# Terminalde okunabilir unicode çıktı istersen
python -m mathpad --pretty "(2+3)*4"

# Pydroid 3 (telefon): terminal gerekmez, bu dosyayı açıp ▶'a bas
pydroid_baslat.py   # çıkışta defter.md / defter.html / defter.txt kaydeder

# 47 soruluk vitrin + otomatik doğrulama
python mathpad_demo.py
```

Kapsam: aritmetik (yüzde/faktöriyel), cebir (denklem sistemleri, diskriminant analizi,
çarpanlara ayırma), kalkülüs (türev, integral, limit, Taylor serisi), lineer cebir
(determinant, ters, özdeğer/özvektör), sayı teorisi (EBOB/EKOK, asallık, kombinasyon),
istatistik (ortalama, medyan, varyans, standart sapma).

Detaylı mimari ve kendi çözücünü yazma rehberi: [mathpad/README bölümü](#mathpad--modüler-akıllı-matematik-çözücü) yerine `mathpad/` paket docstring'lerine ve `demo.py`'ye bak.

---

## Şifreleme Araçları

Tüm araçlar yalnızca standart kütüphaneyi (stdlib) kullanır.

## Yapı

```
.
├── mathpad/                  # MathPad: modüler matematik çözücü paketi
│   ├── engine.py             # Güven skorlu çözücü yönlendirici
│   ├── notebook.py           # LaTeX defter üretimi (md/html/txt)
│   ├── cli.py                # CLI + REPL
│   ├── rendering/            # LaTeX + düz metin katmanları
│   └── solvers/              # 6 değiştirilebilir çözücü
├── mathpad_demo.py           # 47 soruluk doğrulamalı vitrin
├── examples/                 # Demo defter çıktıları
├── base64_tool.py            # Base64 encode/decode
├── caesar_tool.py            # Caesar şifresi (ROT13 dahil)
├── vigenere_tool.py          # Vigenère şifresi
├── xor_tool.py               # XOR şifresi (hex çıktı)
├── hash_tool.py              # md5/sha1/sha256/... özet hesaplama
├── password_gen_tool.py      # Güvenli rastgele şifre üretici
├── requirements.txt          # sympy (MathPad için)
├── tests/                    # 100+ birim testi
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

MathPad demo çıktısını yeniden üretmek için:

```bash
python mathpad_demo.py
```
