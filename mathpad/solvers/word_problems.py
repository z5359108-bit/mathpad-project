"""Sözel problem çözücü: x-bul tipi sayı problemleri ve fonksiyon değerleri."""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import fold_turkmen, try_sympify
from .base import Solution, NoSolverFound, Solver, Step

_NUM = r"(-?\d+(?:[.,]\d+)?)"

# 'sayının 3 katının 5 fazlası 20' -> 3x + 5 = 20
_KAT_FAZLA = re.compile(
    rf"say[iı]n[iı]n?\s*{_NUM}\s*kat[iı]n?[iı]?n?[iı]n?\s*{_NUM}\s*(fazla|eksik|eksi|art)\w*"
    rf"(?:[^0-9-]*?|[^0-9]*?ka[çcd]\w*[^0-9-]*?)\s*(-?\d+(?:[.,]\d+)?)",
    re.IGNORECASE)
# 'sayının 3 katı 24 ise' -> 3x = 24
_KAT = re.compile(rf"say[iı]n[iı]n?\s*{_NUM}\s*kat[iı]\s*(?:[^0-9]*?ka[çcd]\w*)?\s*(-?\d+(?:[.,]\d+)?)", re.IGNORECASE)
# 'sayının yarısı 42' -> x/2 = 42
_YARI = re.compile(rf"say[iı]n[iı]n?\s*(yar[iı]s|yarisi|yarı)\s*(?:[^0-9]*?ka[çcd]\w*)?\s*(-?\d+(?:[.,]\d+)?)", re.IGNORECASE)
# 'iki sayının toplamı 15 farkı 3' -> x+y=15, x-y=3
_IKI_SAYI = re.compile(
    rf"iki\s*say[iı]n?i?n?\s*toplam[iı]\s*(-?\d+(?:[.,]\d+)?)[^.]*?fark[iı]\s*(-?\d+(?:[.,]\d+)?)"
    rf"|iki\s*say[iı]n?i?n?\s*fark[iı]\s*(-?\d+(?:[.,]\d+)?)[^.]*?toplam[iı]\s*(-?\d+(?:[.,]\d+)?)",
    re.IGNORECASE)
# fonksiyon değeri: 'f(x)=3x+2 ... x=2' veya 'f(2) ... f(x)=3x+2' veya 'f(x)=3x+2 fonksiyonunun f(2)'
_FUNC_EQ = re.compile(r"([fg])\s*\(\s*([a-z])\s*\)\s*=\s*([^\s,;]+(?:\s*[\^*/+\-]\s*[^\s,;]+)*)", re.IGNORECASE)
_FUNC_POINT = re.compile(r"([fg])\s*\(\s*(-?\d+(?:[.,]\d+)?)\s*\)", re.IGNORECASE)


class WordProblemSolver(Solver):
    name = "word_problems"
    title = "Sözel problemler"

    def can_handle(self, question: str) -> float:
        q = fold_turkmen(question).lower()
        if re.search(r"f\s*\(\s*g\s*\(|g\s*\(\s*f\s*\(|turev|t\u00fcrev|integral|matris|\[", q):
            return 0.0
        if _KAT_FAZLA.search(q) or _KAT.search(q) or _YARI.search(q) or _IKI_SAYI.search(q):
            return 0.9
        if self._func_value_data(q):
            return 0.85
        return 0.0

    def solve(self, question: str) -> Solution:
        q = fold_turkmen(question).lower()
        func_data = self._func_value_data(q)
        if func_data:
            return self._solve_func_value(question, func_data)
        kat_fazla = _KAT_FAZLA.search(q)
        if kat_fazla:
            return self._solve_kat_fazla(question, kat_fazla)
        iki = _IKI_SAYI.search(q)
        if iki:
            return self._solve_iki_sayi(question, iki)
        kat = _KAT.search(q)
        if kat:
            return self._solve_kat(question, kat)
        yari = _YARI.search(q)
        if yari:
            return self._solve_yari(question, yari)
        raise NoSolverFound(f"Sözel problem kalıbı anlaşılamadı: {question!r}")

    # ------------------------------------------------------------ fonksiyon değeri
    def _func_value_data(self, q: str):
        for match in _FUNC_EQ.finditer(q):
            name, var, expr_text = match.group(1), match.group(2), match.group(3)
            expr = try_sympify(expr_text)
            if expr is None:
                continue
            sym = sp.Symbol(var)
            point = None
            explicit = re.search(rf"{var}\s*=\s*(-?\d+(?:[.,]\d+)?)", q[match.end():])
            if explicit:
                point = sp.Rational(explicit.group(1).replace(",", "."))
            if point is None:
                pt_match = re.search(rf"{name}\s*\(\s*(-?\d+(?:[.,]\d+)?)\s*\)", q)
                if pt_match:
                    point = sp.Rational(pt_match.group(1).replace(",", "."))
            if point is None:
                continue
            return {"name": name, "var": sym, "expr": expr, "point": point}
        return None

    def _solve_func_value(self, question: str, data) -> Solution:
        name, sym, expr, point = data["name"], data["var"], data["expr"], data["point"]
        value = expr.subs(sym, point)
        steps = [
            Step("Fonksiyon", latex=rf"{name}(x) = {to_latex(expr)}"),
            Step("Yerine koy", latex=rf"x = {to_latex(point)}"),
            Step(
                "Hesap",
                latex=rf"{name}({to_latex(point)}) = {to_latex(value)}",
            ),
        ]
        steps.append(Step("Sonuç", content=value))
        return self._solution(
            question, value, steps, f"{name}({point}) fonksiyon değeri")

    # ------------------------------------------------------------ sayı problemleri
    def _solve_kat_fazla(self, question: str, match) -> Solution:
        k = sp.Rational(match.group(1).replace(",", "."))
        extra = sp.Rational(match.group(2).replace(",", "."))
        target = sp.Rational(match.group(4).replace(",", "."))
        sign = "+" if match.group(3).startswith("fazla") or match.group(3).startswith("art") else "-"
        x = sp.Symbol("x")
        lhs = k * x + extra if sign == "+" else k * x - extra
        solution = sp.solve(sp.Eq(lhs, target), x)[0]
        steps = [
            Step("Bilinmeyeni adlandır", latex="sayı = x", detail="istenilen sayı x ile gösterilir"),
            Step(
                "Denklemi kur",
                latex=rf"{to_latex(lhs)} = {to_latex(target)}",
                detail=f"'x'in {k} katının {'fazlas\u0131' if sign == '+' else 'eksigi'} {target} eder",
            ),
            Step(
                "Çöz",
                latex=rf"{to_latex(k)}x = {to_latex(target - extra if sign == '+' else target + extra)}"
                      rf" \Rightarrow x = {to_latex(solution)}",
            ),
            Step(
                "Kontrol",
                latex=rf"{to_latex(k * solution + (extra if sign == '+' else -extra))} = {to_latex(target)} \\checkmark",
            ),
        ]
        steps.append(Step("Sonuç", content=solution))
        return self._solution(question, solution, steps, "Sözel problem: sayıyı bul")

    def _solve_kat(self, question: str, match) -> Solution:
        k = sp.Rational(match.group(1).replace(",", "."))
        target = sp.Rational(match.group(2).replace(",", "."))
        x = sp.Symbol("x")
        solution = sp.solve(sp.Eq(k * x, target), x)[0]
        steps = [
            Step("Bilinmeyeni adlandır", latex="sayı = x"),
            Step("Denklemi kur", latex=rf"{to_latex(k)}x = {to_latex(target)}"),
            Step("Çöz", latex=rf"x = \frac{{{to_latex(target)}}}{{{to_latex(k)}}} = {to_latex(solution)}"),
        ]
        steps.append(Step("Sonuç", content=solution))
        return self._solution(question, solution, steps, "Sözel problem: sayıyı bul")

    def _solve_yari(self, question: str, match) -> Solution:
        target = sp.Rational(match.group(2).replace(",", "."))
        x = sp.Symbol("x")
        solution = sp.solve(sp.Eq(x / 2, target), x)[0]
        steps = [
            Step("Bilinmeyeni adlandır", latex="sayı = x"),
            Step("Denklemi kur", latex=rf"\frac{{x}}{{2}} = {to_latex(target)}"),
            Step("Çöz", latex=rf"x = {to_latex(2 * target)}"),
        ]
        steps.append(Step("Sonuç", content=solution))
        return self._solution(question, solution, steps, "Sözel problem: sayıyı bul")

    def _solve_iki_sayi(self, question: str, match) -> Solution:
        groups = [g for g in match.groups() if g is not None]
        s_total, s_diff = sp.Rational(groups[0].replace(",", ".")), sp.Rational(groups[1].replace(",", "."))
        x, y = sp.Symbol("x"), sp.Symbol("y")
        sols = sp.solve([sp.Eq(x + y, s_total), sp.Eq(x - y, s_diff)], [x, y], dict=True)[0]
        big, small = sols[x], sols[y]
        steps = [
            Step("Değişkenler", latex="büyük sayı = x, \\quad küçük sayı = y"),
            Step(
                "Denklemleri kur",
                latex=rf"x + y = {to_latex(s_total)}, \quad x - y = {to_latex(s_diff)}",
            ),
            Step(
                "Toplamı ve farkı topla",
                latex=rf"2x = {to_latex(s_total + s_diff)} \Rightarrow x = {to_latex(big)}",
            ),
            Step("Yerine koy", latex=rf"y = {to_latex(s_total)} - {to_latex(big)} = {to_latex(small)}"),
            Step("Kontrol", latex=rf"{to_latex(big)} + {to_latex(small)} = {to_latex(s_total)} \\checkmark"),
        ]
        result = f"x = {to_text(big)}, y = {to_text(small)}"
        steps.append(Step("Sonuç", latex=rf"x = {to_latex(big)}, \quad y = {to_latex(small)}"))
        sol = self._solution(question, [big, small], steps, "İki sayı probleminin çözümü")
        sol.result_text = f"büyük sayı x = {result_text_num(big)}, küçük sayı y = {result_text_num(small)}"
        return sol

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


def result_text_num(value) -> str:
    if isinstance(value, sp.Rational) and value.q == 1:
        return str(value.p)
    if value.is_Integer:
        return str(value)
    return f"{float(sp.N(value)):.6g}".rstrip("0").rstrip(".")
