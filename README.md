# MathPad — Modüler Akıllı Matematik Çözücü

Doğal dille yazılan matematik sorularını alıp **adım adım çözen, LaTeX çıktısı
üreten ve sonuçları deftere (Markdown / HTML / düz metin) yazan** modüler Python aracı.
Yalnızca `sympy`'ye dayanır; tüm çözücüler eklenebilir/çıkarılabilir eklenti mimarisindedir.

## Özellikler

| Alan | Yetenek |
|---|---|
| Aritmetik | işlemler, üs/kök, faktöriyel, yüzde (`%15'i 250`, `15% of 80`) |
| Cebir | denklem çözümü (tekli/sistem), ikinci derece + diskriminant analizi, çarpanlara ayırma, açma, basitleştirme |
| Kalkülüs | türev (N. mertebe), belirsiz/belirli integral, limit (±∞ dahil), Taylor/Maclaurin serisi |
| Lineer Cebir | determinant (Sarrus adımı), ters matris, özdeğer/özvektör, rank, iz, transpoze, matris çarpımı |
| İleri Cebir | eşitsizlikler (işaret tablosu, rasyonel), `|2x-3|=7` mutlak değer, log/üstel denklemler (`log_2(x+3)=4`, `3^(x+1)=81`), köklü denklemler (`sqrt(x+5)=x-1` + amaçlı kontrol), arifmetik/geometrik progressiya, Vieta teoremi, özdeşlik uygulaması (`a²+b²=(a+b)²−2ab`), kalan teoremi, binom katsayısı, kompleks sayılar (`(1+2i)(3-i)`, `|3+4i|`) |
| İleri Analiz | teğet denklemi, ekstremumlar (2. türev testi), kapalı aralıkta max/min, eğrilerle sınırlı alan, kısmi integrasyon (`∫x·cosx`, `∫lnx`), yarı açı (`∫sin²x`), u-dönüşümü (`∫x·e^(x²)`), standart limitler (`(e^x−1)/x → 1`) |
| Sayı Teorisi | EBOB/EKOK, asallık testi, asal çarpanlar, bölenler, modüler aritmetik, kombinasyon/permutasyon |
| İstatistik | ortalama, medyan, mod, varyans, standart sapma, toplam, min/max, adet |

- **Türkçe / Türkmençe / İngilizce** soru dili: `x^2 - 3x + 2 = 0`, `deňlemäni çöz: 3x + 4 = 10`, `x^2 fonksiyoniniň hosylayyşyny al`, `derivative of exp(2*x)` — hepsi çalışır.
- **LaTeX çıktı**: her çözüm `$$...$$` bloklarıyla üretilir; HTML defteri MathJax ile tarayıcıda canlı render eder.
- **Akıllı yönlendirme**: motor her çözücünün güven skorunu hesaplar; en iyi çözücü hata verirse sıradakini dener.
- **Kural tabanlı adım adım çözüm** (v1.2): sadece sonuç değil, defterine yazabileceğin kurallı adımlar:
  - Türev: toplama-çıkarma kuralı, sabit × f, çarpım kuralı, kuvvet kuralı, zincir kuralı, türev tablosu
  - İntegral: toplama kuralı, sabit ile çarpım, kuvvet kuralı, `u = ax + b` değişken değiştirme, integral tablosu
  - Limit: 0/0 belirsizlik analizi, ortak çarpan sadeleştirmesi, L'Hôpital kuralı, sonsuzda derece kuralı, trigonometrik limitler (`sin(t)/t → 1`)
  - Cebir: lineer denklemde terim taşıma → bölme → kök → kontrol akışı; ikinci derecede katsayılar + diskriminant formülü + kök formülü
  - Belirli integral defter adımları (v1.3): `dx/(5x+1)` yazımı, `∫_0^1` doğrudan sınırlar, **kesirli sınırlar** (`from 0 to pi/4`, `0 dan 2/3 ye`), kalkülüsün ana teoremi akışı: F(üst) − F(alt) terim terim hesaplanır, `ln(1) = 0` gibi sadeleşmeler not edilir ve sonuç toplanır
  - **Defter zincirleri (v1.4)**: cevaplar okul defterindeki gibi birbirine bağlı derivasyon olarak yazılır, ör. `D=25-16=9, x_{1,2}=(5±3)/4, x_1=2, x_2=1/2`; `x_1+x_2=6, x_1x_2=5 ⟹ x_1²+x_2²=36-10=26`; `f'(x)=2sinx·cosx = sin2x`; `S=∫_0^1(x²-x³)dx=1/3-1/4=1/12`
  - **ASCII/Türkçe/Türkmençe serbest karışım**: `turevi`/`türevi`, `carpanlarina`/`çarpanlarına`, `ikinji onumi`/`ikinci türevi` — hepsi aynı çözücüye gider

## Yapı

```
.
├── mathpad/
│   ├── engine.py            # Yönlendirici motor (güven skorlu çözücü seçimi)
│   ├── notebook.py          # Defter: Markdown + MathJax'lı HTML + düz metin
│   ├── cli.py               # cmd arayüzü (tek soru / REPL)
│   ├── utils.py             # ayrıştırma yardımcıları (implicit çarpım, unicode…)
│   ├── rendering/           # LaTeX ve düz metin katmanları
│   └── solvers/             # değiştirilebilir çözücüler
│       ├── base.py          # Solver arayüzü — kendi çözücünü yaz, register() ile ekle
│       ├── arithmetic.py, algebra.py, calculus.py,
│       ├── advanced_algebra.py, advanced_analysis.py,
│       ├── linear_algebra.py, number_theory.py, statistics.py
├── tests/                   # birim testleri (mathpad: 179; şifreleme araçlarıyla birlikte ~215)
├── examples/                # demo çıktıları (defter.md, defter.html, defter.txt)
├── demo.py                  # 47 soruluk vitrin + doğrulama (repo kopyasında mathpad_demo.py)
└── requirements.txt
```

## Kurulum

```bash
pip install -r requirements.txt   # yalnızca sympy
```

## Kullanım

### Ana menü (önerilen)

Her şey bu menüden yönetilir — soru çözme, defter kaydetme, çıktı biçimi ve ayarlar:

```bash
python mathpad_menu.py
```

```
  1) Soru çöz                  ← tek soru sor, cevabı ayarındaki biçimde al
  2) Serbest mod               ← art arda soru sor ('menu' ile dön)
  3) Defterim                  ← .md/.html/.txt kaydet, PNG döktür, listele
  4) Ayarlar                   ← çıktı biçimi (latex/png/ikisi/pretty), DPI…
  5) Örnek sorular             ← hazır sorulardan dene
  6) Çözücüleri listele
  0) Çıkış                     ← oturumu otomatik deftere kaydeder
```

Ayarlar `ayarlar.json` dosyasına kaydedilir; bir sonraki açışta hatırlanır.

### Komut satırı (script yazacaklar için)

# Deftere kaydet (LaTeX'li Markdown + MathJax HTML)
python -m mathpad --notebook defter.md --html defter.html "x^2 - 3x + 2 = 0"

# Etkileşimli REPL (her cevap LaTeX blokları halinde gelir)
python -m mathpad

# Her çözümü render edilmiş PNG resim olarak kaydet (formüller çizilmiş halde)
python -m mathpad --png resimler "x^2 - 3x + 2 = 0"

# Terminalde okunabilir unicode çıktı istersen
python -m mathpad --pretty "(2+3)*4"

# Çözücüleri listele / zorla seç
python -m mathpad --list
python -m mathpad --solver calculus "d/dx sin(x)*x"
```

> **Not:** Varsayılan çıktı LaTeX'tir; `soru>` REPL'inde ve tek soru modunda
> her çözüm `$$...$$` blokları ile yazılır. Bunlar doğrudan kendi defterine
> (Overleaf, Obsidian, Notion vb. LaTeX destekleyen her yere) kopyalanabilir.
> Terminalde hızlıca okumak istersen `--pretty` bayrağını kullan.
> Ham LaTeX kaynağıyla uğraşmak istemiyorsan `--png` ile her çözümü
> formülleri **çizilmiş** resim dosyası olarak al (matplotlib gerekir).

### Pydroid 3 (telefon)

Pydroid 3'te `pydroid_baslat.py` dosyasını IDE'de açıp ▶ düğmesine bas:
**MathPad ana menüsü** açılır. Menüden:

- `4) Ayarlar` → `1) Çıktı biçimi` → `2) png` seçersen her cevabın formülleri
  **çizilmiş resim** olarak `defter_resim/` klasörüne kaydedilir; Galeri'den
  açıp defterine bakarak yazarsın.
- `ikisi` seçersen hem LaTeX bloğu hem resim üretilir.
- `0) Çıkış` deyince oturumdaki tüm çözümler `defter.md` / `defter.html` /
  `defter.txt` olarak kaydedilir.

İlk kurulumda Pydroid Pip menüsünden `sympy` ve `matplotlib` kur.

Python API:

```python
from mathpad import MathPad, Notebook
from mathpad.rendering.png import solution_to_png

engine = MathPad()
notebook = Notebook()

for soru in ["x^2 - 5x + 6 çarpanlarına ayır", "integral of x^2 from 0 to 3"]:
    notebook.add(engine.ask(soru))

solution = engine.ask("integral of x^2 from 0 to 3")
notebook.add(solution)
solution_to_png(solution, "defter_soru.png")   # render edilmiş formül resmi
notebook.save_html("defter.html")   # tarayıcıda MathJax ile aç
```

Kendi çözücünü eklemek için `Solver` sınıfını genişlet:

```python
from mathpad.solvers.base import Solver

class MySolver(Solver):
    name = "benim"
    def can_handle(self, question) -> float: ...   # 0..1 güven skoru
    def solve(self, question) -> Solution: ...     # adımlı çözüm

engine.register(MySolver())
```

## Testler ve demo

```bash
python -m unittest discover -s tests -v   # 92 test
python demo.py                            # 47 soru, otomatik doğrulamalı
```

Demo çıktısı `examples/defter.md`, `examples/defter.html` ve `examples/defter.txt`
dosyalarına yazılır; son çalıştırmada **47/47 soru çözüldü, 47/47 doğrulandı**.
