"""İstatistik çözücü: ortalama, medyan, mod, standart sapma, varyans, toplam, adet."""

from __future__ import annotations

import re
import statistics as stats

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import extract_numbers
from .base import Solution, Solver, Step

_KW_STRONG = ("ortalama", "mean", "average", "medyan", "median", "mod ", "tepe", "modu",
              "standart sapma", "std", "sapma", "varyans", "variance", "toplam", "sum",
              "adet", "count", "eleman", "min", "maksimum", "maximum", "en küçük", "en büyük")
_KW_WEAK = ("liste", "list", "veri", "data", "sayı", "değer")


def _extract_list(text: str) -> list[float]:
    match = re.search(r"\[([^\[\]]+)\]", text)
    source = match.group(1) if match else text
    source = re.sub(r"(?<=\d),(?=\d\s)", " ", source)
    numbers = extract_numbers(source)
    if not numbers:
        raise ValueError("Soruda sayı listesi bulunamadı; ör: 'ortalama [3, 5, 7]'")
    return numbers


class StatisticsSolver(Solver):
    name = "statistics"
    title = "İstatistik"

    def can_handle(self, question: str) -> float:
        q = question.lower()
        if re.search(r"\[[\d\s,.;-]+\]", q):
            return min(self._score(q, strong=_KW_STRONG, weak=_KW_WEAK) + 0.3, 1.0)
        return self._score(q, strong=_KW_STRONG, weak=_KW_WEAK)

    def solve(self, question: str) -> Solution:
        data = _extract_list(question)
        q = question.lower()
        steps: list[Step] = [
            Step("Veri seti", content=data, detail=f"n = {len(data)}"),
        ]
        if re.search(r"standart sapma|std|sapma", q):
            result = stats.stdev(data) if len(data) > 1 else 0.0
            mean = stats.mean(data)
            steps.append(Step("Ortalama (önce gerekiyor)", content=mean))
            steps.append(Step("Formül", latex="s = \\sqrt{\\frac{\\sum (x_i - \\bar{x})^2}{n - 1}}"))
            title = f"Standart sapma = {self._fmt(result)}"
        elif re.search(r"varyans|variance", q):
            result = stats.variance(data) if len(data) > 1 else 0.0
            steps.append(Step("Formül", latex="s^2 = \\frac{\\sum (x_i - \\bar{x})^2}{n - 1}"))
            title = f"Varyans = {self._fmt(result)}"
        elif re.search(r"medyan|median", q):
            result = stats.median(data)
            steps.append(Step("Sıralama", content=sorted(data)))
            title = f"Medyan = {self._fmt(result)}"
        elif re.search(r"\bmod\b|modu|tepe", q):
            result = stats.multimode(data)
            steps.append(Step("En sık tekrar eden değerler", content=result))
            title = f"Mod = {result}"
        elif re.search(r"toplam|sum", q):
            result = sum(data)
            steps.append(Step("Toplama", latex=" + ".join(self._fmt(x) for x in data)))
            title = f"Toplam = {self._fmt(result)}"
        elif re.search(r"adet|count|eleman", q):
            result = len(data)
            title = f"Eleman sayısı = {result}"
        elif re.search(r"\bmin\b|en küçük", q):
            result = min(data)
            title = f"En küçük = {self._fmt(result)}"
        elif re.search(r"\bmaks?\b|maksimum|maximum|en büyük", q):
            result = max(data)
            title = f"En büyük = {self._fmt(result)}"
        else:
            result = stats.mean(data)
            total = sum(data)
            steps.append(Step("Toplam", latex=" + ".join(self._fmt(x) for x in data) + f" = {self._fmt(total)}"))
            steps.append(Step("Formül", latex=f"\\bar{{x}} = \\frac{{\\sum x_i}}{{n}} = \\frac{{{self._fmt(total)}}}{{{len(data)}}}"))
            title = f"Ortalama = {self._fmt(result)}"
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, title)

    @staticmethod
    def _fmt(value) -> str:
        if isinstance(value, float) and value.is_integer():
            return f"{int(value)}"
        if isinstance(value, float):
            return f"{value:.6g}"
        if isinstance(value, list):
            return "[" + ", ".join(StatisticsSolver._fmt(v) for v in value) + "]"
        return str(value)

    def _solution(self, question: str, result, steps: list[Step], title: str) -> Solution:
        if isinstance(result, list):
            rendered = self._fmt(result)
        elif isinstance(result, (int, float)):
            rendered = self._fmt(result)
        else:
            rendered = str(result)
        return Solution(
            question=question,
            solver=self.name,
            title=title,
            result=result,
            result_tex=rendered,
            result_text=rendered,
            steps=steps,
        )
