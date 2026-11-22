"""İstatistik çözücü: ortalama, medyan, mod, standart sapma, varyans, toplam, adet."""

from __future__ import annotations

import re
import statistics as stats

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import extract_numbers, fold_turkmen
from .base import Solution, Solver, Step

_KW_STRONG = ("ortalama", "mean", "average", "medyan", "median", "mod ", "tepe", "modu",
              "standart sapma", "std", "sapma", "varyans", "variance", "varians", "toplam", "sum",
              "adet", "count", "eleman", "min", "maksimum", "maximum", "en kucuk", "en buyuk",
              "jemi", "orta", "in ulu", "in kici")
_KW_WEAK = ("liste", "list", "veri", "data", "sayi", "deger")


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
        q = fold_turkmen(question).lower()
        if re.search(
            r"funksi\w*|fonksi\w*|aral[iı][ğg]|aralik|interval|noktas|turev|t\u00fcrev|integral|ekstremum|te[gğ]et|f\s*\(", q
        ):
            return 0.0
        if re.search(r"\^\s*\d", question):
            return 0.0
        if re.search(r"\^\s*[a-w]", question):
            return 0.0
        if re.search(r"\b[a-z]\s*=\s*-?\d+\s*(?:to|dan|den)|\bto\s*(?:oo|sonsuz)|\boo\b|yaklasim|seri|serisi|yigilim", q):
            return 0.0
        if re.search(r"(?:sum|toplam)[^\[]{0,60}\b(?:from|[a-z]\s*=)|\bfrom\s+\d+\s+to\b|\bn\s*=\s*\d+\s*(?:to|dan|den)|\b\d+\s*(?:dan|den).{0,20}?\b(?:ya|ye|a|e)\b", q):
            return 0.0
        if re.search(r"det(erminant)?\b|\[\s*\[|matris|matrix|ozdeger|özdeğer|eigen", q):
            return 0.0
        if re.search(r"[a-zA-Z_]{3,}\s*\(", question) and not re.search(
            r"sqrt|sin|cos|tan|log|ln|exp|abs|arcsin|arccos|min\(|max\(", question
        ):
            return 0.0
        if re.search(r"\[[\d\s,.;-]+\]", q):
            return min(self._score(q, strong=_KW_STRONG, weak=_KW_WEAK) + 0.3, 1.0)
        return self._score(q, strong=_KW_STRONG, weak=_KW_WEAK)

    def solve(self, question: str) -> Solution:
        data = _extract_list(question)
        q = fold_turkmen(question).lower()
        steps: list[Step] = [
            Step("Veri seti", content=data, detail=f"n = {len(data)}"),
        ]
        if re.search(r"standart sapma|std|sapma", q):
            mean = stats.mean(data)
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            result = variance ** 0.5
            sample = variance ** 0.5 * (len(data) / (len(data) - 1)) ** 0.5 if len(data) > 1 else result
            steps.append(Step("Ortalama", content=mean))
            steps.append(Step(
                "Formül (popülasyon, n)",
                latex=r"\sigma = \sqrt{\frac{\sum (x_i - \bar{x})^2}{n}}",
            ))
            steps.append(Step(
                "Not (örneklem)",
                latex=f"s = {self._fmt(sample)}",
                detail="n-1 ile bölen örneklem standart sapması; okul çıktısı popülasyon değeridir",
            ))
            title = f"Standart sapma = {self._fmt(result)}"
        elif re.search(r"varians|varyans|variance", q):
            mean = stats.mean(data)
            result = sum((x - mean) ** 2 for x in data) / len(data)
            sample = stats.variance(data) if len(data) > 1 else result
            steps.append(Step("Ortalama", content=mean))
            steps.append(Step(
                "Formül (popülasyon, n)",
                latex=r"\sigma^2 = \frac{\sum (x_i - \bar{x})^2}{n}",
            ))
            steps.append(Step(
                "Not (örneklem varyansı)",
                latex=f"s^2 = \\frac{{\\sum (x_i - \\bar{{x}})^2}}{{n - 1}} = {self._fmt(sample)}",
                detail="n-1 ile bölen örneklem varyansı; okul çıktısı popülasyon değeridir",
            ))
            title = f"Varyans = {self._fmt(result)}"
        elif re.search(r"medyan|median", q):
            result = stats.median(data)
            steps.append(Step("Sıralama", content=sorted(data)))
            title = f"Medyan = {self._fmt(result)}"
        elif re.search(r"\bmod\b|modu|tepe", q):
            result = stats.multimode(data)
            steps.append(Step("En sık tekrar eden değerler", content=result))
            title = f"Mod = {result}"
        elif re.search(r"toplam|sum|jemi", q):
            result = sum(data)
            steps.append(Step("Toplama", latex=" + ".join(self._fmt(x) for x in data)))
            title = f"Toplam = {self._fmt(result)}"
        elif re.search(r"adet|count|eleman", q):
            result = len(data)
            title = f"Eleman sayısı = {result}"
        elif re.search(r"\bmin\b|en kucuk|in kici", q):
            result = min(data)
            title = f"En küçük = {self._fmt(result)}"
        elif re.search(r"\bmaks?\b|maksimum|maximum|en buyuk|in ulu", q):
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
        if isinstance(result, (list, int, float)):
            rendered = self._fmt(result)
        else:
            rendered = str(result)
        return Solution(
            question=question,
            solver=self.name,
            title=title,
            result=result,
            result_tex=to_latex(rendered),
            result_text=rendered,
            steps=steps,
        )
