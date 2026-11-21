"""fuzz_oracle: MathPad'i rastgele uretilmis sorularla dener ve her cevabi
motorun disinda (dogrudan sympy) ayri hesaplayarak dogrular.

Kullanim:  python fuzz_oracle.py [tur_sayisi]
Son satir: "TOPLAM HATA: N" (0 olmali; 0 degilse exit kodu 1).
"""

from __future__ import annotations

import random
import sys

import sympy as sp

x = sp.Symbol("x")

RKATSAYI = (-9, -8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9)
SIFIRSIZ = (-9, -8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9)


def _terim(katsayi, us):
    if us == 0:
        return str(katsayi)
    if us == 1:
        return f"{katsayi}x"
    return f"{katsayi}x^{us}"


def _polinom_metni(usler):
    parcalar = []
    for katsayi, us in usler:
        if katsayi > 0 and parcalar:
            parcalar.append(f"+{_terim(katsayi, us)}")
        elif katsayi < 0:
            parcalar.append(f"-{_terim(abs(katsayi), us)}")
        else:
            parcalar.append(_terim(katsayi, us))
    return "".join(parcalar)


def _usler(r, derece=2):
    ilk = r.choice(SIFIRSIZ)
    usler = [(ilk, derece)]
    for us in range(derece, -1, -1):
        if us == derece:
            continue
        usler.append((r.choice(RKATSAYI) or -4, us))
    return usler


def _sirala(degerler):
    sayilar = [complex(sp.N(v)) for v in degerler]
    return sorted(sayilar, key=lambda z: (round(z.real, 9), round(z.imag, 9)))


def _cift_mi(a, b, tol=1e-8):
    return abs(a - b) <= tol


def _sonuc_degerler(result):
    if isinstance(result, list) and result and isinstance(result[0], dict):
        degerler = [v for cozum in result for v in cozum.values()]
        return _sirala(degerler)
    if isinstance(result, (list, tuple, sp.Tuple)):
        girdi = list(result)
        if all(isinstance(v, (int, float)) or (isinstance(v, sp.Basic) and v.is_number) for v in girdi):
            return _sirala(girdi)
        if len(girdi) == 1 and isinstance(girdi[0], sp.Basic):
            return girdi[0]
        return None
    if isinstance(result, (int, float)) or (isinstance(result, sp.Basic) and result.is_number):
        return _sirala([result])
    if isinstance(result, sp.Basic):
        if result.free_symbols <= {x}:
            return sp.simplify(result)
    return None


def _karsilastir(motor, beklenen):
    if isinstance(motor, sp.Basic) and isinstance(beklenen, sp.Basic):
        return sp.simplify(motor - beklenen) == 0
    if isinstance(motor, list) and isinstance(beklenen, list):
        return len(motor) == len(beklenen) and all(
            _cift_mi(a, b) for a, b in zip(motor, beklenen))
    return False


def uret_denklem(r):
    usler = _usler(r, 2)
    expr = sum(sp.Integer(k) * x**u for k, u in usler)
    soru = f"{_polinom_metni(usler)}=0"
    kokler = sp.Poly(expr, x).all_roots()
    return soru, _sirala(kokler)


def uret_turev(r):
    usler = _usler(r, 3)
    expr = sum(sp.Integer(k) * x**u for k, u in usler)
    soru = f"d/dx {_polinom_metni(usler)}"
    return soru, sp.diff(expr, x)


def uret_integral(r):
    usler = _usler(r, 2)
    expr = sum(sp.Integer(k) * x**u for k, u in usler)
    lo, hi = sorted(r.sample(range(-9, 9), 2))
    soru = f"integral of {_polinom_metni(usler)} from {lo} to {hi}"
    return soru, [sp.integrate(expr, (x, lo, hi))]


def uret_limit(r):
    a = r.choice(SIFIRSIZ)
    b = r.choice(RKATSAYI) or 5
    c = r.choice(RKATSAYI)
    nokta = r.choice([0, 1, 2, -1, -2])
    pay = sp.expand(a * (x - nokta) * (x + b) + c * (x - nokta))
    payda = sp.expand(x - nokta)
    soru = f"lim x->{nokta} ({sp.sstr(pay, sympy_integers=True)})/({sp.sstr(payda, sympy_integers=True)})"
    expr = sp.cancel(pay / payda)
    return soru, [expr.subs(x, nokta)]


def uret_aritmetik(r):
    a1 = r.choice(RKATSAYI)
    d = r.randint(2, 9)
    n = r.choice([5, 10, 20, 30])
    soru = f"arifmetik progressiya: a1={a1}, d={d}. S_{n}=?"
    toplam = (2 * a1 + (n - 1) * d) * sp.Rational(n, 2)
    return soru, [toplam]


def uret_mutlak(r):
    a = r.randint(2, 6)
    b = r.choice(RKATSAYI)
    c = r.randint(2, 12)
    soru = f"|{a}x{('+' if b >= 0 else '')}{b}|={c}"
    kokler = [sp.Rational(c - b, a), sp.Rational(-c - b, a)]
    return soru, _sirala(kokler)


URETICILER = [
    ("denklem", uret_denklem),
    ("turev", uret_turev),
    ("integral", uret_integral),
    ("limit", uret_limit),
    ("progressiya", uret_aritmetik),
    ("mutlak", uret_mutlak),
]


def main():
    tur_sayisi = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    r = random.Random(20260214)
    from mathpad import MathPad

    pad = MathPad()
    toplam = 0
    hatalar = []
    for ad, uret in URETICILER:
        tur_hatasi = 0
        for _ in range(tur_sayisi):
            toplam += 1
            soru, beklenen = uret(r)
            try:
                motor = _sonuc_degerler(pad.ask(soru).result)
            except Exception as exc:  # noqa: BLE001
                tur_hatasi += 1
                hatalar.append(f"[{ad}] {soru} | MOTOR HATASI: {type(exc).__name__}: {exc}")
                continue
            if motor is None:
                continue
            beklenen = (_sirala(beklenen)
                        if isinstance(beklenen, (list, tuple, sp.Tuple))
                        else sp.simplify(beklenen))
            if _karsilastir(motor, beklenen):
                continue
            tur_hatasi += 1
            hatalar.append(f"[{ad}] {soru} | motor: {motor} | dogrusu: {beklenen}")
        print(f"{ad:12s}: {tur_sayisi} soru, {tur_hatasi} hata")
    for satir in hatalar:
        print("HATA:", satir)
    print(f"TOPLAM SORU: {toplam}")
    print(f"TOPLAM HATA: {len(hatalar)}")
    return 1 if hatalar else 0


if __name__ == "__main__":
    sys.exit(main())
