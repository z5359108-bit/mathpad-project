# MathPad — Modüler Akıllı Matematik Çözücü

Doğal dille yazılan matematik sorularını alıp **adım adım çözen, LaTeX çıktısı
üreten ve sonuçları deftere (Markdown / HTML / düz metin) yazan** modüler Python aracı.
Yalnızca `sympy`'ye dayanır; tüm çözücüler eklenebilir/çıkarılabilir eklenti mimarisindedir.

## Özellikler

| Alan | Yetenek |
|---|---|
| Aritmetik | işlemler, üs/kök, faktöriyel, yüzde (`%15'i 250`, `15% of 80`) |
| Cebir | denklem çözümü (tekli/sistem), ikinci derece + diskriminant analizi, çarpanlara ayırma, açma, basitleştirme, polinom bölme (`polinom bolme (x^3-1)/(x-1)` → bölüm+kalan), özdeşlik/boş küme örtüsü (`4x+2=4x+2` → ℝ, `x+1=x+2` → ∅) |
| Kalkülüs | türev (N. mertebe), belirsiz/belirli integral (sınırlarda `e^2`, `pi/2`, `2pi`, `sqrt(2)`), limit (±∞ dahil), Taylor/Maclaurin serisi, toplam/seri (`sum 1/2^n n=1 to oo`, `sum n from 1 to 100`), `int ... dx` kısaltması |
| Lineer Cebir | determinant (Sarrus adımı; kare olmayan matriste açık hata), ters matris, özdeğer/özvektör, rank, iz, transpoze, matris çarpımı |
| İleri Cebir | eşitsizlikler (işaret tablosu, rasyonel), log/üstel **eşitsizlikler** (`log_2(x)<=3` → `(0; 8]`), `|2x-3|=7` mutlak değer (denklem + eşitsizlik), log/üstel denklemler (`log_2(x+3)=4`, `3^(x+1)=81`), köklü denklemler (`sqrt(x+5)=x-1` + amaçlı kontrol), arifmetik/geometrik progressiya, Vieta teoremi, özdeşlik uygulaması (`a²+b²=(a+b)²−2ab`), kalan teoremi, binom katsayısı, kompleks sayılar (`(1+2i)(3-i)`, `|3+4i|`) |
| İleri Analiz | teğet denklemi, ekstremumlar (2. türev testi), kapalı aralıkta max/min, eğrilerle sınırlı alan, dönel cisim hacmi (`y=x^2 x=0..1` → `π/5`), kısmi integrasyon (`∫x·cosx`, `∫lnx`), yarı açı (`∫sin²x`), u-dönüşümü (`∫x·e^(x²)`), standart limitler (`(e^x−1)/x → 1`), `arctan/arcsin` türevleri |
| Sayı Teorisi | EBOB/EKOK, asallık testi, asal çarpanlar, bölenler, modüler aritmetik, kombinasyon/permutasyon |
| İstatistik | ortalama, medyan, mod, **varyans / standart sapma (popülasyon, n; ör. note'da n−1)**, toplam, min/max, adet |
| Geometri | Pisagor/hipotenüs (`3 4 5 dik ucgen` → 5), daire-çember alan/çevre, kare/dikdörtgen/üçgen alan-çevre, küre hacim+yüzey, silindir hacim, küp hacim — π'li sonuçlara yaklaşık ondalık eklenir |
| Sözel Problemler | x-bul tipi sayı problemleri (`bir sayının 3 katının 5 fazlası 20` → 5, yarısı, iki sayı toplam/fark) ve fonksiyon değerleri (`f(x)=3x+2, x=2` → 8) |
| Okul Ekstra | ters trigonometrik değerler (`arcsin(1/2)` → `π/6`), `\|f\|=\|g\|` denklemleri, tanım kümesi (`√`, payda, log), ters fonksiyon (küçük `x³+2` dahil; `x²` için sesli hata), `f(g(x))` kompozisyonu, artan/azalan aralıklar, dönüm noktaları, polinom bölme (bölüm + kalan) |

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
  - **Kısa zincir katmanı (v1.5)**: defter modu artık çözümün LaTeX'ini yamalamaz; her soru ailesi için doğrudan yapısal veriden kısa zincir üretir (`mathpad/rendering/kisa.py`). Başlık, açıklama cümlesi, ondalık yaklaşık değer, türev/integral kural listesi YOKTUR; ham LaTeX komutu ASLA çıkmaz. `MathPad.defter(soru)` ile Python API'den de erişilir. Tanınmayan soru ailesinde açık zincire geri düşer — sessiz çöp üretmez.
  - **Defter PNG render (v1.6)**: defter modunda PNG açıkken zincir satırları artık gerçek mathtext ile çizilir — kesirler alt/üst blok, `√` radikal, `∫₀⁴` sınırlı integral, `⁻¹` gerçek üs. Her satır yapısal olarak mathtext'e çevrilir (`chain_to_mathtext`); çevrilemeyecek satır düz Unicode metin olarak yazılır — PNG'de ham LaTeX komutu asla görünmez. Matematiksel içerik konsoldaki kısa zincirle birebir aynıdır.
  - **Doğrulayıcı katman** (`mathpad/verify.py`): çözücü sonucu döndürmeden önce kökleri denkleme koyar, türevi sayısal farkla, belirli integrali sayısal integrallerle, limiti yakın noktalarla yoklar; ayrıca ters trigonometrik değer, `|f|=|g|` kök kümesi, tanım kümesi örnekleri, ters fonksiyon (`f∘f⁻¹ = x`), kompozisyon, monotonluk aralıkları, dönüm noktaları ve `P = D·q + r` bölünmesini de kontrol eder; tutmazsa cevap yerine açık hata verir.
## Yapı

```
.
├── mathpad/
│   ├── engine.py            # Yönlendirici motor (güven skorlu çözücü seçimi)
│   ├── notebook.py          # Defter: Markdown + MathJax'lı HTML + düz metin
│   ├── cli.py               # cmd arayüzü (tek soru / REPL)
│   ├── utils.py             # ayrıştırma yardımcıları (implicit çarpım, unicode…)
│   ├── rendering/           # LaTeX ve düz metin katmanları
│   │   └── kisa.py         # kısa defter zinciri üreticisi (42 altın soruyla birebir testli)
│   └── solvers/             # değiştirilebilir çözücüler
│       ├── base.py          # Solver arayüzü — kendi çözücünü yaz, register() ile ekle
│       ├── arithmetic.py, algebra.py, calculus.py,
│       ├── advanced_algebra.py, advanced_analysis.py,
│       ├── school_extra.py    # ters trig, |f|=|g|, tanım kümesi, ters fonksiyon,
│       │                      # f(g(x)), artan/azalan, dönüm noktası, bölme
│       ├── linear_algebra.py, number_theory.py, statistics.py
│       ├── geometry.py         # alan/çevre/hacim/hipotenüs (defter adımlı)
│       └── word_problems.py    # x-bul sözel problemleri + f(a) fonksiyon değeri
├── tests/                   # birim testleri (388)
│   └── test_defter_mode.py  # defter modu: soru tipi basina 1 test + kurallar
├── examples/                # demo çıktıları (defter.md, defter.html, defter.txt)
├── mathpad_menu.py          # menü tabanlı ana araç (başlat / ayarlar)
├── pydroid_baslat.py        # Pydroid 3 tek dokunuş başlatıcı
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
  3) Defter modu             ← kısa ders kitabı zinciri (açıklama/ondalık yok)
  4) Defterim                  ← .md/.html/.txt kaydet, PNG döktür, listele
  5) Ayarlar                   ← çıktı biçimi (latex/png/ikisi/pretty), DPI…
  6) Örnek sorular             ← hazır sorulardan dene
  7) Çözücüleri listele
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

# Defter modu: yalnızca kısa matematik zinciri (açıklama/ondalık yok)
python -m mathpad --defter "3x^2-7x+2=0"

# Terminalde okunabilir unicode çıktı istersen
python -m mathpad --pretty "(2+3)*4"

# Her argparse soruyu AYRI bir soru olarak çözer
python -m mathpad.cli --text defter.txt "7!/5!" "dairenin alani r=3" "2x+6=0"

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
python -m unittest discover -s tests -v   # 330 test (test_golden_defter dahil: 42/42)
python fuzz_oracle.py                     # 180 rastgele soru, TOPLAM HATA: 0 olmali
python fuzz_oracle2.py                    # 450 rastgele soru (eşitsizlik, mutlak değer, log/üstel,
                                          # kök, ekstremum, teğet, dizi, integral (e²/π sınırlı), alan,
                                          # limit, türev, diferansiyel, seri), SORU: 450, HATA: 0 olmalı
python demo.py                            # 47 soru, otomatik doğrulamalı
```

Demo çıktısı `examples/defter.md`, `examples/defter.html` ve `examples/defter.txt`
dosyalarına yazılır; son çalıştırmada **47/47 soru çözüldü, 47/47 doğrulandı**.
