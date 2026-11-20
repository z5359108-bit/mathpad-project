"""Kalkülüs çözücü: türev, integral, limit, Taylor serisi."""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..steps import derivative_steps, integral_steps, limit_steps
from ..utils import extract_expression, fold_turkmen, normalize, pick_symbol, try_sympify
from .base import Solution, Solver, Step

_KW_STRONG = ("türev", "derivative", "integral", "limit", "sınır", "taylor",
              "seri", "maclaurin", "d/dx", "∫", "hosylay", "çak", "çek")
_KW_WEAK = ("fonksiyon", "function", "eğri", "yaklaş", "approach", "dx", "açılım", "cek")

_ORDER_WORDS = {"ikinci": 2, "second": 2, "üçüncü": 3, "third": 3, "dördüncü": 4, "fourth": 4}
_BOUND = r"([\w.]+(?:\s*/\s*[\w.]+)?)"
_DEF_TR = re.compile(
    rf"{_BOUND}\s*'?\s*(?:dan|den|tan|ten)\s+{_BOUND}\s*'?\s*(?:ya|ye|a|e)\b"
)
_DEF_EN = re.compile(rf"\bfrom\s*{_BOUND}\s*(?:to|up\s*to)\s*{_BOUND}")
_DEF_SYM = re.compile(r"∫\s*_?\s*\{?\s*([^{}\s,]+)\s*\}?\s*\^\s*\{?\s*([^{}\s,]+)\s*\}?")
_LIMIT = re.compile(r"(\w+)\s*(?:->|→|yaklaşırken|yaklaşınca|approaches|approaching|goes\s*to)\s*(-?[\w.∞]+)")
_NOISE = frozenset({
    "türev", "türevi", "türevini", "derivative", "integral", "integrali", "integralini",
    "al", "alınız", "hesapla", "bul", "nedir", "limit", "limiti", "limitini",
    "sınır", "sınırı", "seri", "serisinin", "açılım", "açılımı", "açılımını", "taylor",
    "maclaurin", "expansion", "series", "dx", "d/dx",
    "fonksiyonunun", "fonksiyonun", "iken", "around", "etrafında", "sıfırda",
    "order", "derece", "terim", "terimli", "terimi", "terms", "derecesi", "mertebeden",
    "birinci", "ikinci", "üçüncü", "dördüncü", "beşinci", "first", "second", "third", "fourth", "fifth",
})


def _order_of(question: str, default: int = 1) -> int:
    q = question.lower()
    for word, n in _ORDER_WORDS.items():
        if word in q:
            return n
    match = re.search(r"(\d+)\s*(?:üncü|ncü|nci|ncı|inci|ıncı)(?:\s*mertebeden)?\s*türev", q)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*\.\s*(?:mertebeden\s*)?türev", q)
    if match:
        return int(match.group(1))
    match = re.search(r"order\s*[:=]?\s*(\d+)", q)
    return int(match.group(1)) if match else default


def _clean_order_phrases(question: str) -> str:
    question = re.sub(r"\d+\s*\.\s*(?:mertebeden\s*)?türev", " türev ", question)
    question = re.sub(r"\b\d+\s*mertebeden\b", " ", question)
    return question


def _bounds(question: str) -> tuple[sp.Basic, sp.Basic, str] | None:
    def to_bound(raw: str) -> sp.Basic | None:
        return sp.Rational(raw) if is_number(raw) else try_sympify(raw)

    for pattern in (_DEF_SYM, _DEF_EN, _DEF_TR):
        match = pattern.search(question)
        if match:
            lower = sp.Rational(match.group(1)) if is_number(match.group(1)) else try_sympify(match.group(1))
            upper = sp.Rational(match.group(2)) if is_number(match.group(2)) else try_sympify(match.group(2))
            if lower is None or upper is None:
                continue
            return lower, upper, match.group(0)
    return None


def is_number(raw: str) -> bool:
    return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", raw))


def _limit_target(question: str) -> tuple[sp.Symbol, sp.Basic, str] | None:
    match = _LIMIT.search(normalize(question))
    if not match:
        return None
    var_name = match.group(1)
    raw_value = match.group(2).lower()
    sign = -1 if raw_value.startswith("-") else 1
    base = raw_value.lstrip("+-")
    infinity_by_name = {"inf": sp.oo, "infinity": sp.oo, "sonsuz": sp.oo, "oo": sp.oo}
    if base in infinity_by_name:
        return sp.Symbol(var_name), sign * infinity_by_name[base], match.group(0)
    value = try_sympify(raw_value)
    if value is None:
        return None
    return sp.Symbol(var_name), value, match.group(0)


def _taylor_params(question: str, default_order: int = 6) -> tuple[sp.Basic, int, str]:
    removed = ""
    point = sp.Integer(0)
    order = default_order
    match = re.search(r"around\s*x?\s*=\s*(-?\d+(?:\.\d+)?)", question.lower())
    if match:
        point = sp.Rational(match.group(1))
        removed += match.group(0) + " "
    match = re.search(r"(\d+)\s*(?:terim\w*|terms?)", question.lower())
    if match:
        order = int(match.group(1))
        removed += match.group(0) + " "
    match = re.search(r"order\s*[:=]?\s*(\d+)", question.lower())
    if match:
        order = int(match.group(1))
        removed += match.group(0) + ""
    match = re.search(r"order\s*[:=]?\s*(\d+)", question.lower())
    if match:
        order = int(match.group(1))
        removed += match.group(0) + " "
    return point, order, removed


class CalculusSolver(Solver):
    name = "calculus"
    title = "Kalkülüs"

    def can_handle(self, question: str) -> float:
        return self._score(fold_turkmen(question).lower(), strong=_KW_STRONG, weak=_KW_WEAK)

    def solve(self, question: str) -> Solution:
        q = fold_turkmen(question).lower()
        if re.search(r"türev|derivative|d/dx|hosylay", q):
            return self._derivative(question)
        if re.search(r"integral|∫", q):
            return self._integral(question)
        if re.search(r"limit|sınır\b|yaklaş|\bçak\b|\bçek\b|\bcek\b", q):
            return self._limit(question)
        if re.search(r"taylor|maclaurin|seri|açılım", q):
            return self._series(question)
        raise ValueError("Kalkülüs alt problemi belirlenemedi.")

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

    def _derivative(self, question: str) -> Solution:
        steps: list[Step] = []
        order = _order_of(question)
        q = re.sub(r"d/dx", " ", question, flags=re.IGNORECASE)
        q = _clean_order_phrases(q)
        candidate = extract_expression(q, extra_noise=_NOISE)
        expr = try_sympify(candidate)
        if expr is None:
            raise ValueError(f"Fonksiyon ayrıştırılamadı: '{candidate}'")
        var = pick_symbol(expr)
        steps.append(Step("Fonksiyon", content=expr, detail=f"değişken: {var.name}"))
        if order != 1:
            steps.append(Step(f"{order}. mertebeden türev isteniyor",
                              latex=f"\\frac{{d^{order}}}{{d{var.name}^{order}}}"))
        steps.append(Step("Türev işlemi",
                          latex=f"\\frac{{d}}{{d{var.name}}}\\left[{to_latex(expr)}\\right]"))
        if order == 1:
            steps.extend(derivative_steps(expr, var))
        else:
            steps.append(Step("Türevi tekrar tekrar uygula",
                              detail=f"{order} kez ardışık türev alınır"))
        result = sp.diff(expr, var, order)
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Türev" if order == 1 else f"{order}. mertebeden türev")

    def _integral(self, question: str) -> Solution:
        steps: list[Step] = []
        bounds = _bounds(question)
        q = question
        if bounds:
            q = q.replace(bounds[2], " ")
        q = re.sub(r"∫", " ", q)
        q = re.sub(r"\bdx\s*/", "1/", q)
        q = re.sub(r"\b(?:from|up\s*to|to)\b", " ", q, flags=re.IGNORECASE)
        candidate = extract_expression(q, extra_noise=_NOISE)
        expr = try_sympify(candidate)
        if expr is None:
            raise ValueError(f"Fonksiyon ayrıştırılamadı: '{candidate}'")
        var = pick_symbol(expr)
        steps.append(Step("Fonksiyon", content=expr, detail=f"değişken: {var.name}"))
        steps.extend(integral_steps(expr, var))
        if bounds:
            lower, upper = bounds[0], bounds[1]
            antiderivative = sp.integrate(expr, var)
            result = sp.integrate(expr, (var, lower, upper))
            steps.insert(1, Step("Belirli integral aralığı",
                                 latex=f"\\int_{{{to_latex(lower)}}}^{{{to_latex(upper)}}}"))
            upper_at = antiderivative.subs(var, upper)
            lower_at = antiderivative.subs(var, lower)
            steps.append(Step(
                "Kalkülüsün ana teoremi: sınırları yerine koy",
                latex=f"\\left[{to_latex(antiderivative)}\\right]_{{{to_latex(lower)}}}^{{{to_latex(upper)}}} = {to_latex(upper_at)} - {to_latex(lower_at)}",
            ))
            steps.append(Step(
                f"Üst sınır: F({to_latex(upper)})",
                latex=f"F({to_latex(upper)}) = {to_latex(upper_at)}",
            ))
            lower_detail = "ln(1) = 0 olduğu için bu terim sadeleşir" if lower == 0 else None
            steps.append(Step(
                f"Alt sınır: F({to_latex(lower)})",
                latex=f"F({to_latex(lower)}) = {to_latex(lower_at)}",
                detail=lower_detail,
            ))
            if lower_at == 0:
                steps.append(Step(
                    "Topla ve sadeleştir",
                    latex=f"{to_latex(upper_at)} - {to_latex(lower_at)} = {to_latex(result)}",
                    detail="sıfır terimi düşer",
                ))
        else:
            result = sp.integrate(expr, var)
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Belirli integral" if bounds else "Belirsiz integral")

    def _limit(self, question: str) -> Solution:
        steps: list[Step] = []
        target = _limit_target(question)
        q = question
        if target:
            var, value, span = target
            q = q.replace(span, " ")
        else:
            expr_probe = try_sympify(extract_expression(q, extra_noise=_NOISE))
            if expr_probe is None:
                raise ValueError("Limit noktası bulunamadı ('x -> 0' gibi bir hedef bekleniyor).")
            var = pick_symbol(expr_probe)
            value = sp.Integer(0)
        candidate = extract_expression(q, extra_noise=_NOISE)
        expr = try_sympify(candidate)
        if expr is None:
            raise ValueError(f"Fonksiyon ayrıştırılamadı: '{candidate}'")
        steps.append(Step("Fonksiyon", content=expr))
        steps.append(Step(f"{var.name} -> {to_latex(value)} hedefi",
                          latex=f"{var.name} \\to {to_latex(value)}"))
        steps.extend(limit_steps(expr, var, value))
        result = sp.limit(expr, var, value, "+-")
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Limit")

    def _series(self, question: str) -> Solution:
        steps: list[Step] = []
        point, order, removed = _taylor_params(question)
        q = question
        for span in removed.split():
            q = q.replace(span, " ", 1)
        q = re.sub(r"\b(?:around|x)\s*=\s*-?\d+(?:\.\d+)?", " ", q, flags=re.IGNORECASE)
        candidate = extract_expression(q, extra_noise=_NOISE)
        expr = try_sympify(candidate)
        if expr is None:
            raise ValueError(f"Fonksiyon ayrıştırılamadı: '{candidate}'")
        var = pick_symbol(expr)
        steps.append(Step("Fonksiyon", content=expr, detail=f"değişken: {var.name}"))
        steps.append(Step("Açılım merkezi ve terim sayısı",
                          latex=f"x_0 = {to_latex(point)},\\; \\text{{terim sayısı}} = {order}"))
        raw = sp.series(expr, var, point, 2 * order + 3).removeO()
        terms = sorted(raw.as_ordered_terms(), key=lambda t: sp.degree(t, gen=var) if t.has(var) else 0)
        result = sp.Add(*terms[:order])
        steps.append(Step("Taylor serisi", content=result))
        return self._solution(question, result, steps, "Taylor serisi açılımı")
