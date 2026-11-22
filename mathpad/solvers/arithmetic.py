"""Aritmetik çözücü: sayısal ifadeler, faktöriyel, yüzde işlemleri."""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import normalize, try_sympify
from .base import Solution, Solver, Step

_PERCENT_AFTER = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|yuzde)", re.IGNORECASE)
_PERCENT_BEFORE = re.compile(r"yuzde\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_PERCENT_PREFIX = re.compile(r"%\s*(\d+(?:\.\d+)?)")
_FACTORIAL = re.compile(r"(?<![\w.])(\d+)\s*!")


def parse_percent(question: str) -> tuple[float, float] | None:
    """Soru içinde yüzde ilişkisi varsa (oran, taban) döndür.

    Desteklenen biçimler: '%15'i 250', '250'nin %15'i', '15% of 250', 'yüzde 15 i 250'.
    """
    match = _PERCENT_PREFIX.search(question) or _PERCENT_AFTER.search(question) \
        or _PERCENT_BEFORE.search(question)
    if not match:
        return None
    rate = float(match.group(1))
    numbers = [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", question)]
    others = [n for n in numbers if abs(n - rate) > 1e-12]
    if len(others) != 1:
        return None
    return rate, others[0]


class ArithmeticSolver(Solver):
    name = "arithmetic"
    title = "Aritmetik"

    _ALLOWED_WORDS = {"sqrt", "sin", "cos", "tan", "cot", "log", "exp", "ln", "abs", "pi", "oo", "mod"}
    _NOISE_WORDS = re.compile(
        r"\b(?:what|is|the|of|calculate|compute|hesapla|bul|nedir|kac|kaç|kactir|result|eşittir)\b",
        re.IGNORECASE,
    )

    def can_handle(self, question: str) -> float:
        if parse_percent(question):
            return 0.95
        if _FACTORIAL.search(question):
            return 0.9
        cleaned = self._NOISE_WORDS.sub(" ", normalize(question)).strip().strip(",. ")
        if not cleaned or "=" in cleaned:
            return 0.0
        unknown_words = [
            token for token in re.findall(r"[A-Za-zçğıöşüÇĞİÖŞÜ_]{2,}", cleaned)
            if token.lower() not in self._ALLOWED_WORDS
        ]
        if unknown_words:
            return 0.0
        value = try_sympify(cleaned)
        if value is None:
            return 0.0
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", cleaned):
            return 0.85
        if re.search(r"\d|[a-zA-Z]", cleaned) and (re.search(r"[+\-*/^!()]", cleaned) or _FACTORIAL.search(cleaned)):
            return 0.8
        return 0.0

    def solve(self, question: str) -> Solution:
        steps: list[Step] = []

        percent = parse_percent(question)
        if percent:
            rate, base = percent
            value = sp.Rational(str(base)) * sp.Rational(str(rate)) / 100
            steps.append(Step(
                "Sorunun okunuşu",
                latex=f"\\%{self._fmt(rate)} \\text{{ oranı, }} {self._fmt(base)} \\text{{ tabanı ile}}",
            ))
            steps.append(Step(
                "Yüzde formülü",
                latex=f"\\frac{{{self._fmt(base)} \\cdot {self._fmt(rate)}}}{{100}}",
            ))
            steps.append(Step("Sonuç", content=value))
            return self._solution(
                question, value, steps,
                title=f"Yüzde hesabı: {self._fmt(base)} sayısının %{self._fmt(rate)}'i",
            )

        factorials = _FACTORIAL.findall(question)
        if factorials and not parse_percent(question):
            text = _FACTORIAL.sub(lambda m: f" factorial({m.group(1)}) ", question)
            text = re.sub(
                r"\b(?:what|is|the|calculate|hesapla|kac|kaç|kactir|nedir|eşittir|result|bul|compute)\b",
                " ", text, flags=re.IGNORECASE,
            )
            parsed = try_sympify(text.strip())
            if parsed is not None:
                steps.append(Step(
                    "Faktöriyel tanımı",
                    latex=", \\quad ".join(f"{n}! = 1 \\cdot 2 \\cdots {n}" for n in factorials)))
                value = sp.simplify(parsed)
                steps.append(Step("Hesap", content=value))
                if len(factorials) > 1:
                    title = "Faktöriyel işlemi: " + " / ".join(f"{n}!" for n in factorials)
                else:
                    title = f"Faktöriyel: {factorials[0]}!"
                return self._solution(question, value, steps, title=title)

        text = re.sub(
            r"\b(?:what|is|calculate|hesapla|kac|kaç|nedir|eşittir|result|bul|compute)\b",
            " ", question, flags=re.IGNORECASE,
        )
        parsed = try_sympify(text)
        if parsed is None:
            raise ValueError("Sayısal ifade ayrıştırılamadı.")
        steps.append(Step("Verilen işlem", content=parsed))
        value = sp.simplify(parsed)
        if value.has(sp.zoo) or value == sp.nan:
            raise ValueError("İşlem tanımsız (sıfıra bölme içeriyor).")
        steps.append(Step("Sonuç", content=value))
        return self._solution(question, value, steps, title="Aritmetik işlem")

    @staticmethod
    def _fmt(value: float) -> str:
        return f"{value:g}".replace(",", ".")

    def _solution(self, question: str, result, steps: list[Step], title: str) -> Solution:
        return Solution(
            question=question,
            solver=self.name,
            title=title,
            result=result,
            result_tex=to_latex(result),
            result_text=to_text(result),
            steps=steps,
        )
