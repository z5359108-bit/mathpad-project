# zeyrox_projects

Kişisel Python araçları ve test ortamı.

## Yapı

```
.
├── base64_tool.py        # Base64 encode/decode aracı
├── tests/
│   └── test_base64_tool.py
└── .gitignore
```

## Kullanım

```bash
# Metni kodla
python base64_tool.py encode "Selam Dünya"

# Base64'ü çöz
python base64_tool.py decode "U2VsYW0gRMO8bnlh"

# Dosyadan oku
python base64_tool.py encode -f dosya.txt
```

## Testler

```bash
python -m unittest discover -s tests -v
```
