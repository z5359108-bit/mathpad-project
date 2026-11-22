"""Geometri çözücü: hipotenüs, alan/çevre, hacim — okul defterine hazır adımlarla."""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import fold_turkmen
from .base import Solution, Solver, Step


def _num(raw: str) -> sp.Basic:
    raw = raw.replace(",", ".")
    return sp.Rational(raw)


class GeometrySolver(Solver):
    name = "geometry"
    title = "Geometri"

    _SHAPES = {
        "hipotenus": r"hipotenus|hypotenuse|ipsilnus",
        "daire": r"daire|\u00e7ember|ember|circle",
        "kare": r"\bkare\b|\bkarenin\b|square",
        "dikdortgen": r"dikdortgen|rectangle",
        "ucgen": r"ucgen|\u00fc\u00e7gen|triangle",
        "kure": r"kure|k\u00fcre|sphere",
        "silindir": r"silindir|cylinder",
        "kup": r"\bk[u\u00fc]p\w*|cube",
        "eskenar_dortgen": r"eskenar dortgen|rhombus",
    }

    _ACTIONS = {
        "alan": r"\balan\w*|\barea\b|\bsurface\b|y\u00fczey",
        "cevre": r"\bcevre\w*|\bperimeter\b|\b\u00e7evre\b",
        "hacim": r"hac\w*|\bvolume\b",
        "hipotenus": r"hipot\w*",
    }

    def can_handle(self, question: str) -> float:
        q = fold_turkmen(question).lower()
        if "x" in q.replace(" ", "") and "=" in q and not re.search(r"\br\s*=|\bh\s*=|kenar", q):
            return 0.0
        if re.search(r"f\s*\(|turev|t\u00fcrev|integral|matris|\[", q):
            return 0.0
        shape = self._shape(q)
        action = self._action(q)
        if shape and action:
            return 0.85
        if shape == "hipotenus":
            return 0.85
        if action is None and re.search(r"dik\s*ucgen|right\s+triangle", q) \
                and len(self._plain_numbers(q)) >= 2:
            return 0.7
        return 0.0

    def _shape(self, q: str) -> str | None:
        for name, pattern in self._SHAPES.items():
            if re.search(pattern, q):
                return name
        return None

    def _action(self, q: str) -> str | None:
        for name, pattern in self._ACTIONS.items():
            if re.search(pattern, q):
                return name
        return None

    def solve(self, question: str) -> Solution:
        q = fold_turkmen(question).lower()
        shape = self._shape(q)
        action = self._action(q)
        if shape == "hipotenus":
            action = None
        handler = {
            ("hipotenus", None): self._hypotenuse,
            ("daire", "alan"): self._circle_area,
            ("daire", "cevre"): self._circle_circumference,
            ("daire", "hacim"): self._sphere_volume,
            ("kure", "hacim"): self._sphere_volume,
            ("kure", "alan"): self._sphere_area,
            ("kare", "alan"): self._square_area,
            ("kare", "cevre"): self._square_perimeter,
            ("dikdortgen", "alan"): self._rectangle_area,
            ("dikdortgen", "cevre"): self._rectangle_perimeter,
            ("ucgen", "alan"): self._triangle_area,
            ("silindir", "hacim"): self._cylinder_volume,
            ("kup", "hacim"): self._cube_volume,
        }
        if action is None and shape in (None, "ucgen", "hipotenus") \
                and re.search(r"dik\s*ucgen|right\s+triangle", q):
            return self._hypotenuse(question, q)
        if shape == "ucgen" and re.search(r"hipot\w*", q):
            handler_key = ("hipotenus", None)
        else:
            handler_key = (shape, action) if (shape, action) in handler else (shape, action)
        func = handler.get(handler_key)
        if func is None:
            raise ValueError(
                f"Bu geometri sorusu desteklenmiyor: '{question}'. "
                "\u00d6rnek: 'dairenin alan\u0131 r=3', 'dik \u00fc\u00e7gen hipoten\u00fcs kenarlar 3 ve 4'.")
        return func(question, q)

    # ------------------------------------------------------------- hipotenüs
    def _hypotenuse(self, question: str, q: str) -> Solution:
        nums = self._labeled_numbers(q, ("dik kenar", "kenar", "kenarlar"))
        if len(nums) < 2:
            raise ValueError("İki dik kenar gerekli; ör: 'dik üçgen dik kenarları 3 ve 4, hipotenüs'.")
        a, b = nums[0], nums[1]
        steps = [
            Step("Pisagor teoremi", latex=r"c^2 = a^2 + b^2"),
            Step(
                "Yerine koy",
                latex=rf"c^2 = {to_latex(a)}^2 + {to_latex(b)}^2 = {to_latex(a**2 + b**2)}",
            ),
            Step(
                "Hipotenüs",
                latex=rf"c = \sqrt{{{to_latex(a**2 + b**2)}}} = {to_latex(sp.sqrt(a**2 + b**2))}",
            ),
        ]
        result = sp.sqrt(a**2 + b**2)
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Hipotenüs (Pisagor)")

    # ------------------------------------------------------------- daire
    def _circle_area(self, question: str, q: str) -> Solution:
        r = self._radius(q)
        steps = [
            Step("Daire alanı formülü", latex=r"A = \pi r^2"),
            Step(
                "Yerine koy",
                latex=rf"A = \pi \cdot {to_latex(r)}^2 = {to_latex(sp.pi * r**2)}",
            ),
        ]
        result = sp.pi * r**2
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Dairenin alanı")

    def _circle_circumference(self, question: str, q: str) -> Solution:
        r = self._radius(q)
        steps = [
            Step("Çevre formülü", latex=r"C = 2\pi r"),
            Step("Yerine koy", latex=rf"C = 2 \pi \cdot {to_latex(r)} = {to_latex(2 * sp.pi * r)}"),
        ]
        result = 2 * sp.pi * r
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Dairenin çevresi")

    # ------------------------------------------------------------- küre/silindir/küp
    def _sphere_volume(self, question: str, q: str) -> Solution:
        r = self._radius(q)
        steps = [
            Step("Küre hacmi formülü", latex=r"V = \frac{4}{3}\pi r^3"),
            Step(
                "Yerine koy",
                latex=rf"V = \frac{{4}}{{3}} \pi \cdot {to_latex(r)}^3 = {to_latex(sp.Rational(4, 3) * sp.pi * r**3)}",
            ),
        ]
        result = sp.Rational(4, 3) * sp.pi * r**3
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Kürenin hacmi")

    def _sphere_area(self, question: str, q: str) -> Solution:
        r = self._radius(q)
        steps = [
            Step("Küre yüzey alanı formülü", latex=r"A = 4\pi r^2"),
            Step("Yerine koy", latex=rf"A = 4 \pi \cdot {to_latex(r)}^2 = {to_latex(4 * sp.pi * r**2)}"),
        ]
        result = 4 * sp.pi * r**2
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Kürenin yüzey alanı")

    def _cylinder_volume(self, question: str, q: str) -> Solution:
        r = self._radius(q)
        heights = self._labeled_numbers(q, ("yukseklik", "yükseklik", "h"))
        if not heights:
            raise ValueError("Silindir yüksekliği gerekli; ör: 'silindir hacmi r=2 h=5'.")
        h = heights[0]
        steps = [
            Step("Silindir hacmi formülü", latex=r"V = \pi r^2 h"),
            Step(
                "Yerine koy",
                latex=rf"V = \pi \cdot {to_latex(r)}^2 \cdot {to_latex(h)} = {to_latex(sp.pi * r**2 * h)}",
            ),
        ]
        result = sp.pi * r**2 * h
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Silindirin hacmi")

    def _cube_volume(self, question: str, q: str) -> Solution:
        nums = self._labeled_numbers(q, ("kenar",))
        if not nums:
            raise ValueError("Küp kenarı gerekli; ör: 'küp hacmi kenar 3'.")
        a = nums[0]
        steps = [
            Step("Küp hacmi formülü", latex=r"V = a^3"),
            Step("Yerine koy", latex=rf"V = {to_latex(a)}^3 = {to_latex(a**3)}"),
        ]
        result = a**3
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Küpün hacmi")

    # ------------------------------------------------------------- poligonlar
    def _square_area(self, question: str, q: str) -> Solution:
        a = self._one_side(q)
        steps = [
            Step("Kare alanı formülü", latex=r"A = a^2"),
            Step("Yerine koy", latex=rf"A = {to_latex(a)}^2 = {to_latex(a**2)}"),
        ]
        result = a**2
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Karenin alanı")

    def _square_perimeter(self, question: str, q: str) -> Solution:
        a = self._one_side(q)
        steps = [
            Step("Kare çevre formülü", latex=r"P = 4a"),
            Step("Yerine koy", latex=rf"P = 4 \cdot {to_latex(a)} = {to_latex(4 * a)}"),
        ]
        result = 4 * a
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Karenin çevresi")

    def _rectangle_area(self, question: str, q: str) -> Solution:
        a, b = self._two_sides(q)
        steps = [
            Step("Dikdörtgen alanı formülü", latex=r"A = a \cdot b"),
            Step(
                "Yerine koy",
                latex=rf"A = {to_latex(a)} \cdot {to_latex(b)} = {to_latex(a * b)}",
            ),
        ]
        result = a * b
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Dikdörtgenin alanı")

    def _rectangle_perimeter(self, question: str, q: str) -> Solution:
        a, b = self._two_sides(q)
        steps = [
            Step("Dikdörtgen çevre formülü", latex=r"P = 2(a + b)"),
            Step(
                "Yerine koy",
                latex=rf"P = 2({to_latex(a)} + {to_latex(b)}) = {to_latex(2 * (a + b))}",
            ),
        ]
        result = 2 * (a + b)
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Dikdörtgenin çevresi")

    def _triangle_area(self, question: str, q: str) -> Solution:
        nums = self._labeled_numbers(q, ("taban", "yukseklik", "yükseklik", "kenar"))
        if len(nums) < 2:
            raise ValueError("Taban ve yükseklik gerekli; ör: 'üçgen alan taban 6 yükseklik 4'.")
        b, h = nums[0], nums[1]
        steps = [
            Step("Üçgen alanı formülü", latex=r"A = \frac{1}{2} \cdot taban \cdot yükseklik"),
            Step(
                "Yerine koy",
                latex=rf"A = \frac{{1}}{{2}} \cdot {to_latex(b)} \cdot {to_latex(h)} = {to_latex(b * h / 2)}",
            ),
        ]
        result = b * h / 2
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Üçgenin alanı")

    # ------------------------------------------------------------- yardımcılar
    def _radius(self, q: str):
        match = re.search(r"\br\s*=\s*(-?\d+(?:[.,]\d+)?)", q)
        if match:
            return _num(match.group(1))
        match = re.search(r"yar[iı]\s*[\u00e7c]a[pğ]\w*\s*(?:is\s*)?(-?\d+(?:[.,]\d+)?)|yar[iı]cap\w*\s*=?\s*(-?\d+(?:[.,]\d+)?)", q)
        if match:
            return _num(match.group(1) or match.group(2))
        nums = self._plain_numbers(q)
        if len(nums) == 1:
            return nums[0]
        raise ValueError("Yarıçap bulunamadı; ör: 'dairenin alanı r=3'.")

    def _one_side(self, q: str):
        nums = self._labeled_numbers(q, ("kenar",))
        if not nums:
            nums = self._plain_numbers(q)
        if len(nums) == 1:
            return nums[0]
        raise ValueError("Tek kenar değeri bulunamadı.")

    def _two_sides(self, q: str):
        for pattern in (r"kenar\w*\s*(\d+(?:[.,]\d+)?)\s*(?:ve|i|ile)?\s*(\d+(?:[.,]\d+)?)",
                        r"(\d+(?:[.,]\d+)?)\s*(?:ve|i|ile|birbirinden)?\s*(\d+(?:[.,]\d+)?)\s+kenar"):
            match = re.search(pattern, q)
            if match:
                return _num(match.group(1)), _num(match.group(2))
        nums = self._plain_numbers(q)
        if len(nums) >= 2:
            return nums[0], nums[1]
        raise ValueError("İki kenar değeri bulunamadı.")

    def _labeled_numbers(self, q: str, labels) -> list:
        nums = []
        seen_spans = set()
        for label in labels:
            match = re.search(rf"{label}\w*\s*=?\s*(-?\d+(?:[.,]\d+)?)", q)
            if match and match.start(1) not in seen_spans:
                seen_spans.add(match.start(1))
                nums.append(_num(match.group(1)))
        if len(nums) < 2:
            for n in self._plain_numbers(q):
                if n not in nums:
                    nums.append(n)
                if len(nums) >= 2:
                    break
        return nums

    @staticmethod
    def _plain_numbers(q: str) -> list:
        raw = re.findall(r"-?\d+(?:[.,]\d+)?", q)
        return [_num(x) for x in raw]

    def _solution(self, question: str, result, steps: list[Step], title: str) -> Solution:
        approx = ""
        if result.has(sp.pi):
            approx = f" \\\\approx {float(sp.N(result)):.4g}"
        return Solution(
            question=question,
            solver=self.name,
            title=title,
            result=result,
            result_tex=to_latex(result) + approx,
            result_text=to_text(result) + (f"  (yaklaşık {float(sp.N(result)):.4f})" if approx else ""),
            steps=steps,
        )
