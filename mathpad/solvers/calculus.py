"""Kalkülüs çözücü: türev, integral, limit, Taylor serisi."""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..steps import derivative_steps, integral_steps, limit_steps
from ..utils import extract_expression, fold_turkmen, normalize, pick_symbol, try_sympify
from .base import NoSolverFound, Solution, Solver, Step

_KW_STRONG = ("turev", "türev", "derivative", "integral", "limit", "sinir", "sınır", "taylor",
              "seri", "maclaurin", "d/dx", "∫", "hosylay", "cak", "cek", "onumi", "onum", "turev", "differensial", "differensialyn", "differensialyny", "diferensial", "diferensialyn", "diferensialyny", "diferensiyal", "diferensiyalyn", "diferensiyalyny", "diferansiyel", "lim")
_KW_WEAK = ("fonksiyon", "function", "egri", "yaklas", "approach", "dx", "acilim", "cek")

_ORDER_WORDS = {"ikinci": 2, "ikinji": 2, "second": 2,
                "ucuncu": 3, "uchunji": 3, "third": 3,
                "dorduncu": 4, "dordunji": 4, "fourth": 4}
_BOUND = r"(-?(?:[\w.\^*/π−]+|\s*\([^()]*\)|\s*/\s*[\w.]+)+)"
_DEF_TR = re.compile(
    rf"{_BOUND}[\s'-]*(?:dan|den|tan|ten)\s+{_BOUND}[\s'-]*(?:ya|ye|a|e)\b"
)
_DEF_PAREN = re.compile(rf"\(\s*{_BOUND}\s*to\s*{_BOUND}\s*\)")
_DEF_EN = re.compile(rf"\bfrom\s*{_BOUND}\s*(?:to|up\s*to)\s*{_BOUND}")
_DEF_SYM = re.compile(r"∫\s*_\s*\{?\s*([^{}\s,]+)\s*\}?\s*\^\s*\{?\s*([^{}\s,]+)\s*\}?")
_DEF_ARROW = re.compile(r"∫\s*\(\s*([^→()\s]+)\s*→\s*([^)\s]+)\s*\)")
_LIMIT = re.compile(r"(\w+)\s*(?:->|\u2192|yaklas?i[rğ]?[en]*k?e?n?|yaklasi[rğ]?[en]*|approaches|approaching|goes\s*to|tends\s+to)\s*(-?[\w.∞]+[+-]?)")
_PIPES_TO_ABS = re.compile(r"\|([^|]+)\|")
_NOISE = frozenset({
    "türev", "türevi", "türevini", "derivative", "integral", "integrali", "integralini",
    "integralyny", "integralyn", "integralynyn",
    "al", "alınız", "hesapla", "bul", "nedir", "limit", "limiti", "limitini",
    "sınır", "sınırı", "seri", "serisinin", "açılım", "açılımı", "açılımını", "taylor",
    "maclaurin", "expansion", "series", "dx", "d/dx", "at",
    "fonksiyonunun", "fonksiyonun", "iken", "around", "etrafında", "sıfırda",
    "order", "derece", "terim", "terimli", "terimi", "terms", "derecesi", "mertebeden",
    "birinci", "ikinci", "üçüncü", "dördüncü", "beşinci", "first", "second", "third", "fourth", "fifth",
    "ikinji", "onum", "onumi", "önümi", "funksiyanyn", "funksiyanin", "funksiyanynyn",
    "turev", "turevi", "turevini", "turevleri", "turevleri",
    "differensial", "differensialyny", "differensialyn",
    "tapyn", "tapy", "tap", "tapmaly", "tapmag",
    "lim", "diferensial", "diferensialyny", "diferensialyn",
    "diferensiyal", "diferensiyalyny", "diferensiyalyn",
})


def _order_of(question: str, default: int = 1) -> int:
    q = fold_turkmen(question).lower()
    for word, n in sorted(_ORDER_WORDS.items(), key=lambda item: -item[1]):
        if re.search(rf"\b{word}\b", q):
            return n
    match = re.search(r"(\d+)\s*(?:unc?u|inc?i|nc[uüiı])(?:\s*mertebeden)?\s*(?:turev|türev)", q)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*\.\s*(?:mertebeden\s*)?(?:turev|türev)", q)
    if match:
        return int(match.group(1))
    match = re.search(r"order\s*[:=]?\s*(\d+)", q)
    return int(match.group(1)) if match else default


def _clean_order_phrases(question: str) -> str:
    question = re.sub(r"\d+\s*\.\s*(?:mertebeden\s*)?(?:turev|türev)", " turev ", question)
    question = re.sub(r"\b\d+\s*mertebeden\b", " ", question)
    return question


def _bounds(question: str) -> tuple[sp.Basic, sp.Basic, str] | None:
    def to_bound(raw: str) -> sp.Basic | None:
        raw = raw.replace("−", "-").strip()
        if is_number(raw):
            return sp.Rational(raw)
        return try_sympify(raw)

    for pattern in (_DEF_SYM, _DEF_PAREN, _DEF_EN, _DEF_TR, _DEF_ARROW):
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


def _limit_target(question: str) -> tuple[sp.Symbol, sp.Basic, str, str] | None:
    match = _LIMIT.search(normalize(question))
    if not match:
        return None
    var_name = match.group(1)
    raw_value = match.group(2).lower()
    direction = ""
    if len(raw_value) > 1 and raw_value[-1] in "+-":
        direction = raw_value[-1]
        raw_value = raw_value[:-1]
    sign = -1 if raw_value.startswith("-") else 1
    base = raw_value.lstrip("+-")
    infinity_by_name = {"inf": sp.oo, "infinity": sp.oo, "sonsuz": sp.oo, "oo": sp.oo}
    if base in infinity_by_name:
        return sp.Symbol(var_name), sign * infinity_by_name[base], match.group(0), direction
    value = try_sympify(raw_value)
    if value is None:
        return None
    return sp.Symbol(var_name), value, match.group(0), direction


def _taylor_params(question: str, default_order: int = 6) -> tuple[sp.Basic, int, str]:
    removed = ""
    point = sp.Integer(0)
    order = default_order
    match = re.search(r"(?:around|at|civarinda|civar\u0131nda|civar\u0131nda\w*|etraf\u0131nda)\s*x?\s*=?\s*(-?\d+(?:\.\d+)?)", question.lower())
    if match:
        point = sp.Rational(match.group(1))
        removed += match.group(0) + " "
    match = re.search(r"\bat\s+(-?\d+(?:\.\d+)?)", question.lower())
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
        q = fold_turkmen(question).lower()
        if re.search(r"[fgyh]\s*['′]\s*\(\s*[a-z]\s*\)", q):
            if re.search(r"[fgyh]\s*\(\s*[a-z]\s*\)\s*=", q):
                return 0.85
            return 0.7
        if re.search(r"\(\s*[^()]+?\s*\)\s*['′]", q):
            return 0.85
        if re.search(r"\bsum\s+\S+\s+[a-z]\s*=\s*\S+\s+to\b", q):
            return 0.92
        if re.search(r"\bsum\s+[a-z]\s*=|\bsumm|\bsum\s+[a-z]\s+[-\d]|\u03a3\s*_", q):
            return 0.85
        if re.search(r"\bsum\s+[a-z]\s+from\s+[^=]*?\bto\b", q):
            return 0.9
        if re.search(r"\bint\s+\S+\s*(?:d\s*[a-z])\b", q):
            return 0.85
        if re.search(r"\bdf\s*[:=]\s*", q):
            return 0.9
        if re.search(r"\bd\s*\(\s*[^()]+?\s*\)", q):
            return 0.9
        if re.search(r"\bdf\b", q) and re.search(r"[fbg]\s*\(\s*[a-z]\s*\)\s*=", q):
            return 0.9
        return self._score(q, strong=_KW_STRONG, weak=_KW_WEAK)

    def solve(self, question: str) -> Solution:
        q = fold_turkmen(question).lower()
        if re.search(r"\bdf\s*:\s*", q):
            question = re.sub(r"\bdf\s*:\s*", "diferensial ", question)
            return self._derivative(question, differential=True)
        if re.search(r"\bdf\b", q) and re.search(r"[fbg]\s*\(\s*[a-z]\s*\)\s*=", q):
            question = re.sub(r"\s*,?\s*\bdf\b\s*", " ", question)
            return self._derivative("diferensial " + question, differential=True)
        df_eq = re.search(r"\bdf\s*=\s*\(?([^()]+?)\)?\s*dx\b", question, re.IGNORECASE)
        if df_eq:
            return self._antiderivative_from_df(question, df_eq.group(1))
        dform = re.search(r"\bd\s*\(([^()]*)\)(?!\s*=)", question)
        if dform and dform.group(1).strip():
            return self._derivative(f"diferensial f(x) = {dform.group(1)}", differential=True)
        prime_postfix = re.search(r"\(\s*([^()]+?)\s*\)\s*['′]", q)
        if prime_postfix and not re.search(r"integral|limit|\blimb|\bsin|\bcos", q):
            return self._derivative(
                question[:prime_postfix.start()] + " turev " + prime_postfix.group(1) + " "
                + question[prime_postfix.end():])
        if re.search(r"[fgy]\s*['′]\s*\(\s*[a-z]\s*\)", q) and re.search(r"[fgy]\s*\(\s*[a-z]\s*\)\s*=", q):
            return self._derivative(re.sub(r"[fgy]\s*['′]\s*\([^)]*\)", " ", question))
        sum_from = re.search(
            r"\bsum\s+([a-zA-Z])\s+from\s+([\-\w.]+)\s+to\s+([\-\w.]+)\s*(?:of\s+|for\s+)?(.*)$",
            question, re.IGNORECASE)
        if sum_from:
            expr_part = sum_from.group(4).strip() or sum_from.group(1)
            normalized = (question[:sum_from.start()]
                          + f"sum {sum_from.group(1)}={sum_from.group(2)} to {sum_from.group(3)} of {expr_part}"
                          + question[sum_from.end():])
        else:
            normalized = re.sub(
                r"\b(summation|sum)\s+([a-zA-Z])\s*=?\s*([\-\w.]+)\s+(?:to\s+)?([\-\w.]+)\s+(?:of\s+)?(.+)",
                r"sum \2=\3 to \4 of \5", question, flags=re.IGNORECASE)
        series_swapped = re.search(
            r"\bsum\s+(.+)\s+([a-zA-Z])\s*=\s*([\-\w./]+)\s+to\s+([\-\w./]+)\s*$",
            normalized, re.IGNORECASE)
        if series_swapped:
            normalized = (normalized[:series_swapped.start()]
                          + f"sum {series_swapped.group(2)}={series_swapped.group(3)} to {series_swapped.group(4)} of {series_swapped.group(1)}")
        sum_match = re.search(
            r"\bsum\s+([a-zA-Z])\s*=\s*([\-\w.]+)\s+to\s+([\-\w.]+)\s+(?:of\s+)?(.+)",
            normalized, re.IGNORECASE)
        if sum_match:
            return self._finite_sum(question, sum_match)
        if re.search(r"\bsummation\b", q):
            raise NoSolverFound(
                "Sonsuz toplam istegi anlasilamadi; ornek: 'sum k=1 to 10 of k^2'.")
        if "summa" in q or "Σ" in q:
            return self._series(question)
        if re.search(r"türev|turev|derivative|d/dx|hosylay|ikinji|onum|differensial|diferensial|diferensiyal|diferansiyel", q):
            return self._derivative(
                question,
                differential=bool(re.search(
                    r"differensial|diferensial|diferensiyal|diferansiyel", q)),
            )
        if re.search(r"\bint\s+\S+\s*(?:d\s*[a-z])\b|integral|∫", q):
            if re.search(r"\bint\s+\S+\s*(?:d\s*[a-z])\b", q):
                question = re.sub(r"\bint\s+", "integral ", question)
            return self._integral(question)
        if re.search(r"limit|lim\b|sınır\b|sinir\b|yaklaş|yaklas|\bçak\b|\bcak\b|\bçek\b|\bcek\b", q):
            return self._limit(question)
        if re.search(r"taylor|maclaurin|seri|açılım|acilim", q):
            return self._series(question)
        raise ValueError("Kalkülüs alt problemi belirlenemedi.")

    def _solution(self, question: str, result, steps: list[Step], title: str,
                  data: dict | None = None) -> Solution:
        return Solution(
            question=question,
            solver=self.name,
            title=title,
            result=result,
            result_tex=to_latex(result),
            result_text=to_text(result),
            steps=steps,
            data=data or {},
        )

    def _derivative(self, question: str, differential: bool = False) -> Solution:
        steps: list[Step] = []
        order = _order_of(question)
        question = re.sub(r"\b(?:y|f|g)\s*\(\s*([a-z])\s*\)\s*=\s*", " ", question, flags=re.IGNORECASE)
        question = _PIPES_TO_ABS.sub(r"abs(\1)", question)
        q = re.sub(r"d/dx", " ", question, flags=re.IGNORECASE)
        q = _clean_order_phrases(q)
        candidate = extract_expression(q, extra_noise=_NOISE)
        expr = try_sympify(candidate)
        if expr is None:
            raise ValueError(f"Fonksiyon ayrıştırılamadı: '{candidate}'")
        if expr.atoms(sp.Abs):
            real_map = {s: sp.Symbol(s.name, real=True) for s in expr.free_symbols}
            if real_map:
                expr = expr.subs(real_map)
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
        combined = result
        if order == 1 and isinstance(expr, sp.Mul) and any(
            isinstance(part, sp.Pow) and bool(part.exp.is_negative) for part in expr.args
        ):
            merged = sp.cancel(sp.together(result))
            if merged != result:
                steps.append(Step("Ortak paydaya getir", content=merged))
                combined = merged
        trig = sp.trigsimp(result)
        if trig != result:
            _latex = to_latex
            steps.append(Step(
                "Trigonometrik özdeşlik",
                latex=rf"{_latex(result)} = {_latex(trig)}",
            ))
            combined = trig
        result = combined
        if differential:
            dx = sp.Symbol("dx")
            steps.append(Step("Diferensiyal",
                              latex=rf"df = {to_latex(result)}\,dx",
                              detail="diferensiyal = türev × dx"))
            result = result * dx
        steps.append(Step("Sonuç", content=result))
        title = "Diferensiyal" if differential else ("Türev" if order == 1 else f"{order}. mertebeden türev")
        return self._solution(question, result, steps, title, data={
            "kind": "derivative", "expr": expr, "var": var,
            "order": order, "result": result,
        })

    def _antiderivative_from_df(self, question: str, inner: str) -> Solution:
        expr = try_sympify(inner.strip())
        if expr is None:
            raise ValueError(f"Diferansiyel form ayrıştırılamadı: 'df = ({inner})dx'")
        var = pick_symbol(expr)
        F = sp.integrate(expr, var)
        result = F + sp.Symbol("C")
        steps = [
            Step("Denklem", latex=rf"df = ({to_latex(expr)})\,dx",
                 detail="df = f\u2032(x)\u00b7dx demektir"),
            Step("İki tarafın integralini al", latex=rf"f = \int {to_latex(expr)}\,d{var.name}"),
            Step("İntegrali hesapla", latex=rf"f = {to_latex(F)} + C"),
        ]
        return self._solution(question, result, steps, "Diferansiyel formdan fonksiyon (antitürev)")

    def _integral(self, question: str) -> Solution:
        question = re.sub(r"\b(?:y|f|g)\s*\(\s*([a-z])\s*\)\s*=\s*", " ", question, flags=re.IGNORECASE)
        steps: list[Step] = []
        bounds = _bounds(question)
        q = question
        if bounds:
            q = q.replace(bounds[2], " ")
        q = re.sub(r"∫", " ", q)
        q = re.sub(r"\bdx\s*/", "1/", q)
        q = re.sub(r"\bdx\b", " ", q)
        q = re.sub(r"\b(?:from|up\s*to|to|cenli|çenli)\b", " ", q, flags=re.IGNORECASE)
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
            divergent = result == sp.nan or result.has(sp.oo) or result == sp.zoo
            if divergent:
                singulars = []
                try:
                    num, den = sp.together(expr).as_numer_denom()
                    singulars = [r for r in sp.solve(sp.Eq(den, 0), var)
                                 if r.is_real and (lower <= r <= upper)]
                except Exception:  # noqa: BLE001
                    singulars = []
                steps.append(Step("Tekillik kontrolü",
                                  latex=", ".join(rf"{to_latex(var)} = {to_latex(r)}" for r in singulars),
                                  detail="aralık içinde integrande tanımsızlık var"))
                steps.append(Step("Iraksak integral",
                                  latex=r"\text{integral yakınsak değil}",
                                  detail="sonuç sonlu değil; bu integral yakınsak değildir"))
                result = "Iraksak integral (yakınsak değil)"
            else:
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
        return self._solution(
            question, result, steps,
            "Belirli integral" if bounds else "Belirsiz integral",
            data={
                "kind": "integral", "expr": expr, "var": var,
                "bounds": (bounds[0], bounds[1]) if bounds else None,
                "result": result,
            },
        )

    def _limit(self, question: str) -> Solution:
        steps: list[Step] = []
        target = _limit_target(question)
        q = question
        if target:
            var, value, span, direction = target
            q = q.replace(span, " ")
        else:
            expr_probe = try_sympify(extract_expression(q, extra_noise=_NOISE))
            if expr_probe is None:
                raise ValueError("Limit noktası bulunamadı ('x -> 0' gibi bir hedef bekleniyor).")
            var = pick_symbol(expr_probe)
            value = sp.Integer(0)
            direction = ""
        candidate = extract_expression(q, extra_noise=_NOISE)
        expr = try_sympify(candidate)
        if expr is None:
            raise ValueError(f"Fonksiyon ayrıştırılamadı: '{candidate}'")
        steps.append(Step("Fonksiyon", content=expr))
        if direction in ("+", "-"):
            side = "+" if direction == "+" else "-"
            detail = "sağdan yaklaşıyor (x → a⁺)" if direction == "+" else "soldan yaklaşıyor (x → a⁻)"
            steps.append(Step("Yönlü limit",
                              latex=f"\\lim_{{{var.name} \\to {to_latex(value)}{side}}} \\left({to_latex(expr)}\\right)",
                              detail=detail))
        steps.append(Step(f"{var.name} -> {to_latex(value)} hedefi",
                          latex=f"{var.name} \\to {to_latex(value)}"))
        steps.extend(limit_steps(expr, var, value))
        result = sp.limit(expr, var, value, direction if direction else "+-")
        if not direction and (result == sp.zoo or result == sp.nan):
            left = sp.limit(expr, var, value, "-")
            right = sp.limit(expr, var, value, "+")
            steps.append(Step("Soldan limit",
                              latex=rf"\lim_{{{var.name} \to {to_latex(value)}^-}} = {to_latex(left)}"))
            steps.append(Step("Sağdan limit",
                              latex=rf"\lim_{{{var.name} \to {to_latex(value)}^+}} = {to_latex(right)}"))
            if left != right:
                steps.append(Step("Limit mevcut değil",
                                  latex="\\lim_{x \\to a} f(x) \\nexists",
                                  detail=f"sol değer {to_text(left)}, sağ değer {to_text(right)}; ikisi farklı"))
                return self._solution(question, "Limit mevcut değil (sol ve sağ limitler farklı)",
                                      steps, "Limit (yok)")
            result = left
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Limit", data={
            "kind": "limit", "expr": expr, "var": var,
            "point": value, "direction": direction, "result": result,
        })

    def _finite_sum(self, question: str, match) -> Solution:
        steps: list[Step] = []
        var_name, lo_raw, hi_raw, body_raw = match.groups()
        var = sp.Symbol(var_name.lower())
        lo = sp.Rational(lo_raw) if is_number(lo_raw) else try_sympify(lo_raw)
        hi = sp.Rational(hi_raw) if is_number(hi_raw) else try_sympify(hi_raw)
        body = try_sympify(body_raw)
        if body is None or lo is None or hi is None:
            raise ValueError("Toplam sinirlari veya terimi ayristirilamadi.")
        steps.append(Step("Genel terim", content=body,
                          detail=f"{var.name} = {lo} ... {hi}"))
        result = sp.summation(body, (var, lo, hi))
        steps.append(Step("Sonuc", content=result))
        return self._solution(question, result, steps, "Sonlu toplam (sum)", data={
            "kind": "series", "expr": body, "var": var,
            "bounds": (lo, hi), "result": result,
        })

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
