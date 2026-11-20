"""Sayı teorisi çözücü: EBOB/EKOK, asallık, çarpanlara ayırma, mod, kombinasyon."""

from __future__ import annotations

import math
import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import extract_numbers, fold_turkmen, replace_decimal_comma
from .base import Solution, Solver, Step

_KW_STRONG = ("ebob", "obeb", "gcd", "ekok", "okek", "lcm", "asal", "prime", "carpanla", "çarpanla",
              "factoriz", "faktör", "mod", "kalan", "kombinasyon", "permutasyon", "permutation",
              "combination", "bölthünen", "bölünebilirlik")
_KW_WEAK = ("sayi", "sayı", "number", "tam", "bolen", "bölen", "divisor")

_COMB = re.compile(r"\bC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)|(\d+)\s*[Cc]\s*(\d+)\b", re.IGNORECASE)
_PERM = re.compile(r"\bP\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)|(\d+)\s*[Pp]\s*(\d+)\b", re.IGNORECASE)
_MOD = re.compile(r"(-?\d+)\s*\^\s*(\d+)\s*(?:mod|%%)\s*(\d+)|(\d+)\s*(?:%|mod)\s*(\d+)")


class NumberTheorySolver(Solver):
    name = "number_theory"
    title = "Sayı Teorisi"

    def can_handle(self, question: str) -> float:
        q = fold_turkmen(question).lower()
        if re.search(r"polinom|b[oö]lünd[uü][kg]ünde", q):
            return 0.0
        if _COMB.search(q) or _PERM.search(q) or _MOD.search(q):
            return 0.9
        if re.search(r"ebob|obeb|gcd|ekok|okek|lcm|asal|prime|kombinasyon|permutasyon|carpanla|factoriz|bolegi|boluji", q):
            return 0.85
        return self._score(q, strong=_KW_STRONG, weak=_KW_WEAK)

    def solve(self, question: str) -> Solution:
        q = fold_turkmen(question).lower()
        if re.search(r"ebob|obeb|gcd", q):
            numbers = self._ints(question, min_count=2)
            return self._gcd(numbers, question)
        if re.search(r"ekok|okek|lcm", q):
            numbers = self._ints(question, min_count=2)
            return self._lcm(numbers, question)
        if re.search(r"asal m[iı]|asalmi|is\s*prime|prime\?|asallik|asallık", q):
            return self._prime(question)
        if re.search(r"carpanla|factoriz|asal [cç]arpan|faktor", q):
            return self._factorization(question)
        if re.search(r"bolen|divisor", q):
            numbers = self._ints(question, min_count=1)
            return self._divisors(numbers[0], question)
        if re.search(r"kombinasyon", q):
            numbers = [int(n) for n in re.findall(r"\d+", q)]
            if len(numbers) < 2:
                raise ValueError("Kombinasyon için n ve k gerekiyor; ör: '10'un 3'lü kombinasyonu'.")
            return self._combination(numbers[0], numbers[1], question)
        if re.search(r"permutasyon", q):
            numbers = [int(n) for n in re.findall(r"\d+", q)]
            if len(numbers) < 2:
                raise ValueError("Permütasyon için n ve k gerekiyor; ör: '5'in 2'li permutasyonu'.")
            return self._permutation(numbers[0], numbers[1], question)
        if _COMB.search(question):
            n, k = self._comb_args(question)
            return self._combination(n, k, question)
        if _PERM.search(question):
            n, k = self._perm_args(question)
            return self._permutation(n, k, question)
        mod = _MOD.search(replace_decimal_comma(question))
        if mod:
            return self._modulo(mod, question)
        numbers = self._ints(question, min_count=2)
        return self._gcd(numbers, question)

    def _ints(self, question: str, min_count: int) -> list[int]:
        numbers = [int(n) for n in re.findall(r"-?\d+", replace_decimal_comma(question))
                   if float(n).is_integer()]
        if len(numbers) < min_count:
            raise ValueError(f"En az {min_count} tam sayı gerekiyor.")
        return numbers

    def _solution(self, question: str, result, steps: list[Step], title: str,
                  result_tex: str | None = None) -> Solution:
        return Solution(
            question=question,
            solver=self.name,
            title=title,
            result=result,
            result_tex=result_tex or to_latex(result),
            result_text=to_text(result),
            steps=steps,
        )

    def _gcd(self, numbers: list[int], question: str) -> Solution:
        steps: list[Step] = []
        n1, n2 = numbers[0], numbers[1]
        steps.append(Step("Veriler", latex=f"\\gcd({n1}, {n2})"))
        value = math.gcd(abs(n1), abs(n2))
        steps.append(Step("Öklid algoritması",
                          latex=f"\\gcd({n1}, {n2}) = \\gcd({n2}, {n1 % n2}) = {value}"))
        return self._solution(question, value, steps, f"EBOB({n1}, {n2}) = {value}")

    def _lcm(self, numbers: list[int], question: str) -> Solution:
        steps: list[Step] = []
        n1, n2 = numbers[0], numbers[1]
        gcd = math.gcd(abs(n1), abs(n2))
        value = abs(n1 * n2) // gcd if gcd else 0
        steps.append(Step("Formül", latex=f"\\operatorname{{EKOK}}(a, b) = \\frac{{|a \\cdot b|}}{{\\gcd(a, b)}}"))
        steps.append(Step("Hesap", latex=f"\\frac{{|{n1} \\cdot {n2}|}}{{{gcd}}} = {value}"))
        return self._solution(question, value, steps, f"EKOK({n1}, {n2}) = {value}")

    def _prime(self, question: str) -> Solution:
        steps: list[Step] = []
        numbers = self._ints(question, min_count=1)
        n = numbers[0]
        is_prime = sp.isprime(n)
        steps.append(Step("Test edilen sayı", latex=f"n = {n}"))
        if is_prime:
            steps.append(Step("Sonuç", latex=f"{n} \\text{{ asaldır}}"))
            detail = f"{n} asaldır."
        else:
            factors = sp.factorint(n)
            factor_str = " \\cdot ".join(f"{base}^{exp}" if exp > 1 else str(base) for base, exp in factors.items())
            steps.append(Step("Asal olmayan — çarpanları", latex=f"{n} = {factor_str}"))
            detail = f"{n} asal değildir (çarpanları: {factor_str.replace(' \\cdot ', ' · ')})."
        return self._solution(question, detail, steps, f"{n} asal mı?", result_tex=to_latex(detail))

    def _factorization(self, question: str) -> Solution:
        steps: list[Step] = []
        numbers = self._ints(question, min_count=1)
        n = numbers[0]
        factors = sp.factorint(n)
        steps.append(Step("Sayı", latex=f"n = {n}"))
        expanded = " \\cdot ".join(
            f"({base}^{{{exp}}})" if exp > 1 else str(base) for base, exp in factors.items()
        )
        steps.append(Step("Asal çarpanlar", latex=f"{n} = {expanded}"))
        result_str = " · ".join(f"{base}^{exp}" if exp > 1 else str(base) for base, exp in factors.items())
        return self._solution(question, result_str, steps,
                              f"{n} sayısının asal çarpanları", result_tex=f"{n} = {expanded}")

    def _divisors(self, n: int, question: str) -> Solution:
        steps: list[Step] = [Step("Sayı", latex=f"n = {n}")]
        divisors = sorted(sp.divisors(n))
        steps.append(Step("Tüm bölenler", content=divisors))
        return self._solution(question, divisors, steps, f"{n} sayısının bölenleri")

    def _comb_args(self, question: str):
        match = _COMB.search(question)
        nums = [g for g in match.groups() if g]
        return int(nums[0]), int(nums[1])

    def _perm_args(self, question: str):
        match = _PERM.search(question)
        nums = [g for g in match.groups() if g]
        return int(nums[0]), int(nums[1])

    def _combination(self, n: int, k: int, question: str) -> Solution:
        steps: list[Step] = [Step("Veriler", latex=f"C({n}, {k})")]
        steps.append(Step("Formül", latex=f"C(n, k) = \\frac{{n!}}{{k!(n-k)!}} = \\frac{{{n}!}}{{{k}!\\cdot{n-k}!}}"))
        value = sp.binomial(n, k)
        steps.append(Step("Hesap", content=value))
        return self._solution(question, value, steps, f"C({n}, {k}) = {value}")

    def _permutation(self, n: int, k: int, question: str) -> Solution:
        steps: list[Step] = [Step("Veriler", latex=f"P({n}, {k})")]
        steps.append(Step("Formül", latex=f"P(n, k) = \\frac{{n!}}{{(n-k)!}} = \\frac{{{n}!}}{{{n-k}!}}"))
        value = sp.factorial(n) // sp.factorial(n - k)
        steps.append(Step("Hesap", content=value))
        return self._solution(question, value, steps, f"P({n}, {k}) = {value}")

    def _modulo(self, match: re.Match, question: str) -> Solution:
        if match.group(4) is not None:
            base, mod = int(match.group(4)), int(match.group(5))
            steps = [Step("Veriler", latex=f"{base} \\bmod {mod}")]
            value = sp.Mod(base, mod)
            steps.append(Step("Bölümden kalan", content=value))
            title = f"{base} mod {mod} = {value}"
        else:
            base, exp, mod = int(match.group(1)), int(match.group(2)), int(match.group(3))
            steps = [Step("Veriler", latex=f"{base}^{{{exp}}} \\bmod {mod}")]
            value = pow(base, exp, mod)
            steps.append(Step("Hesap", latex=f"{base}^{{{exp}}} \\bmod {mod} = {value}"))
            title = f"{base}^{exp} mod {mod} = {value}"
        return self._solution(question, value, steps, title)
