#!/usr/bin/env python3
"""MathPad vitrin: motoru farklı soru tipleriyle zorlayan uçtan uca demo."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sympy as sp

from mathpad import MathPad, Notebook

x, y = sp.Symbol("x"), sp.Symbol("y")
I = sp.I


def expr_eq(result, expected) -> bool:
    try:
        return sp.simplify(sp.sympify(result) - expected) == 0
    except (sp.SympifyError, TypeError, ValueError):
        return False


def close(result, expected) -> bool:
    try:
        return abs(float(result) - expected) < 1e-9
    except (TypeError, ValueError):
        return False


def mat_eq(result, expected) -> bool:
    try:
        diff = sp.Matrix(result) - sp.Matrix(expected)
        return diff == sp.zeros(*diff.shape)
    except (TypeError, ValueError, sp.SympifyError):
        return False


QUESTIONS = [
    # aritmetik
    "(2+3)*4 - 7/2",
    "2^10 + sqrt(144)",
    "sqrt(2)*sqrt(8)",
    "5!",
    "250'nin %15'i",
    "15% of 80",
    # cebir
    "3*x + 4 = 10 denklemini çöz",
    "x^2 - 3x + 2 = 0",
    "x^2 + 1 = 0 (karmaşık kökler)",
    "x + y = 5, x - y = 1",
    "x^2 - 5x + 6 çarpanlarına ayır",
    "(x + 2)*(x + 3) expand",
    "simplify (x^2 - 1)/(x - 1)",
    # kalkülüs
    "x^3 + 2*x fonksiyonunun türevi",
    "d/dx sin(x)*exp(x)",
    "x^4 ikinci türev",
    "integral of x^2 dx",
    "integral of x^2 from 0 to 3",
    "sin(x) fonksiyonunun 0 dan pi ye integrali",
    "limit of sin(x)/x as x->0",
    "x->2 iken (x^2-4)/(x-2) limiti",
    "limit of (3*x + 1)/x as x->inf",
    "limit of 2^(1/x) as x->inf",
    "taylor series of sin(x), 5 terms",
    "taylor series of exp(x), 4 terms",
    # lineer cebir
    "[[1,2],[3,4]] matrisinin determinantı",
    "[[4,7],[2,6]] inverse",
    "[[2,0],[0,3]] özdeğerleri ve özvektörleri",
    "[[1,2],[3,4]] [[5,6],[7,8]] çarpımı",
    "[[2,1],[1,3]] izi",
    "[[1,2],[2,4]] rank",
    # sayı teorisi
    "gcd(48, 18)",
    "ekok(4, 6)",
    "97 asal mı?",
    "91 asal mı?",
    "360 sayısını asal çarpanlarına ayır",
    "12 sayısının bölenleri",
    "7^3 mod 100",
    "C(10, 3)",
    "P(5, 2)",
    # istatistik
    "ortalama [1, 2, 3, 4, 5]",
    "medyan [1, 2, 3, 100]",
    "varyans [2, 4, 4, 4, 5, 5, 7, 9]",
    "standart sapma [2, 4, 4, 4, 5, 5, 7, 9]",
    "modu [1, 2, 2, 3, 3, 3]",
    "toplam [10, 20, 30, 40]",
    "en büyük değer [3, 9, 2]",
]

VERIFICATIONS = {
    "(2+3)*4 - 7/2": lambda s: expr_eq(s.result, sp.Rational(33, 2)),
    "2^10 + sqrt(144)": lambda s: close(s.result, 1036),
    "sqrt(2)*sqrt(8)": lambda s: close(s.result, 4),
    "5!": lambda s: close(s.result, 120),
    "250'nin %15'i": lambda s: close(s.result, 37.5),
    "15% of 80": lambda s: close(s.result, 12),
    "3*x + 4 = 10 denklemini çöz": lambda s: expr_eq(next(iter(s.result[0].values())), 2),
    "x^2 - 3x + 2 = 0": lambda s: {1, 2} == {next(iter(row.values())) for row in s.result},
    "x^2 + 1 = 0 (karmaşık kökler)": lambda s: {I, -I} == {next(iter(row.values())) for row in s.result},
    "x + y = 5, x - y = 1": lambda s: (3, 2) in {tuple(map(int, row.values())) for row in s.result},
    "x^2 - 5x + 6 çarpanlarına ayır": lambda s: expr_eq(s.result, (x - 2) * (x - 3)),
    "(x + 2)*(x + 3) expand": lambda s: expr_eq(s.result, x**2 + 5*x + 6),
    "simplify (x^2 - 1)/(x - 1)": lambda s: expr_eq(s.result, x + 1),
    "x^3 + 2*x fonksiyonunun türevi": lambda s: expr_eq(s.result, 3*x**2 + 2),
    "d/dx sin(x)*exp(x)": lambda s: expr_eq(s.result, sp.exp(x) * sp.sin(x) + sp.exp(x) * sp.cos(x)),
    "x^4 ikinci türev": lambda s: expr_eq(s.result, 12*x**2),
    "integral of x^2 dx": lambda s: expr_eq(s.result, x**3 / 3),
    "integral of x^2 from 0 to 3": lambda s: close(s.result, 9),
    "sin(x) fonksiyonunun 0 dan pi ye integrali": lambda s: close(s.result, 2),
    "limit of sin(x)/x as x->0": lambda s: close(s.result, 1),
    "x->2 iken (x^2-4)/(x-2) limiti": lambda s: close(s.result, 4),
    "limit of (3*x + 1)/x as x->inf": lambda s: close(s.result, 3),
    "limit of 2^(1/x) as x->inf": lambda s: close(s.result, 1),
    "taylor series of sin(x), 5 terms": lambda s: expr_eq(
        s.result, x - x**3/6 + x**5/120 - x**7/5040 + x**9/362880),
    "taylor series of exp(x), 4 terms": lambda s: expr_eq(s.result, 1 + x + x**2/2 + x**3/6),
    "[[1,2],[3,4]] matrisinin determinantı": lambda s: close(s.result, -2),
    "[[4,7],[2,6]] inverse": lambda s: mat_eq(s.result, sp.Matrix([[sp.Rational(3, 5), sp.Rational(-7, 10)],
                                                                   [sp.Rational(-1, 5), sp.Rational(2, 5)]])),
    "[[2,0],[0,3]] özdeğerleri ve özvektörleri": lambda s: {2, 3} <= set(map(int, s.result["özdeğerler"])),
    "[[1,2],[3,4]] [[5,6],[7,8]] çarpımı": lambda s: mat_eq(s.result, sp.Matrix([[19, 22],
                                                                                  [43, 50]])),
    "[[2,1],[1,3]] izi": lambda s: close(s.result, 5),
    "[[1,2],[2,4]] rank": lambda s: close(s.result, 1),
    "gcd(48, 18)": lambda s: close(s.result, 6),
    "ekok(4, 6)": lambda s: close(s.result, 12),
    "97 asal mı?": lambda s: "asaldır" in s.result_text,
    "91 asal mı?": lambda s: "değildir" in s.result_text,
    "360 sayısını asal çarpanlarına ayır": lambda s: all(t in s.result_text for t in ("2^3", "3^2", "5")),
    "12 sayısının bölenleri": lambda s: [1, 2, 3, 4, 6, 12] == [int(v) for v in s.result],
    "7^3 mod 100": lambda s: close(s.result, 43),
    "C(10, 3)": lambda s: close(s.result, 120),
    "P(5, 2)": lambda s: close(s.result, 20),
    "ortalama [1, 2, 3, 4, 5]": lambda s: close(s.result, 3),
    "medyan [1, 2, 3, 100]": lambda s: close(s.result, 2.5),
    "varyans [2, 4, 4, 4, 5, 5, 7, 9]": lambda s: close(s.result, 32 / 7),
    "standart sapma [2, 4, 4, 4, 5, 5, 7, 9]": lambda s: close(s.result, (32 / 7) ** 0.5),
    "modu [1, 2, 2, 3, 3, 3]": lambda s: 3.0 in s.result,
    "toplam [10, 20, 30, 40]": lambda s: close(s.result, 100),
    "en büyük değer [3, 9, 2]": lambda s: close(s.result, 9),
}


def main() -> int:
    engine = MathPad()
    notebook = Notebook(title="MathPad Demo Defteri")

    solved = failed = verified = 0
    for question in QUESTIONS:
        try:
            solution = engine.ask(question)
            notebook.add(solution)
            solved += 1
            check = VERIFICATIONS.get(question)
            status = ""
            if check:
                ok = bool(check(solution))
                status = " ✓ (doğrulandı)" if ok else " ✗ YANLIŞ SONUÇ"
                verified += ok
            short = " ".join(str(solution.result_text).split())[:58]
            print(f"[{solved:2d}] {question}  =>  {short}{status}")
        except Exception as exc:
            failed += 1
            print(f"[--] {question}  =>  HATA: {exc}")

    print("-" * 60)
    print(f"çözülen: {solved}/{len(QUESTIONS)}, doğrulanan: {verified}/{len(VERIFICATIONS)}, hata: {failed}")

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")
    os.makedirs(base, exist_ok=True)
    print("defter:", notebook.save_markdown(os.path.join(base, "defter.md")))
    print("html:  ", notebook.save_html(os.path.join(base, "defter.html")))
    print("metin: ", notebook.save_text(os.path.join(base, "defter.txt")))
    return 1 if failed or verified < len(VERIFICATIONS) else 0


if __name__ == "__main__":
    sys.exit(main())
