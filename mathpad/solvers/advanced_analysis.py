"""İleri analiz çözücü: teğet denklemi, ekstremum, kapalı aralıkta en
büyük/en küçük değer, eğrilerle sınırlı alan.

Kısmi integrasyon, yarı açı ve (e^x−1)/x standart limiti steps.py katmanında
tanımlıdır; bu modül kalkülüsün kapsamadığı okul konularını ekler.
"""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..steps import derivative_steps
from ..utils import fold_turkmen, normalize, pick_symbol, try_sympify
from .base import Solution, Solver, Step

_NOISE_AN = r"\b(?:solve|çöz|coz|hesapla|bul|nedir|soruy?|fonksiyonunun|fonksiyonun|funksiyanyn|funksiyanin|eğrisine|egrisine|çyzyklary|cyzyklary|bilen|çäklenen|ceklenen|aral[ğg][ıi]n[d]?[a]?|noktas[ıi]ndaki|noktasinda)\b"
_INTERVAL_RE = re.compile(r"[\[\(]\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*[\]\)]")
_POINT_RE = re.compile(r"x_?0?\s*=\s*(-?\d+(?:\.\d+)?)")
_KEEP_TOKENS = {
    "sin", "cos", "tan", "cot", "sec", "csc", "exp", "ln", "log", "pi",
    "sqrt", "abs", "asin", "acos", "atan", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "oo", "inf",
}


def _mathify(raw: str) -> str:
    """Uzun saf alfabetik sözcükleri (fonksiyonunun, egrisinin...) atar."""
    tokens = []
    for tok in raw.strip().split():
        core = tok.lower()
        if len(core) >= 3 and core.isalpha() and not (core[-1].isdigit() and "_" in core):
            if core not in _KEEP_TOKENS:
                continue
        tokens.append(tok)
    return " ".join(tokens)


def _norm(question: str) -> str:
    return fold_turkmen(normalize(question)).lower()


def _L(expr) -> str:
    return sp.latex(expr, ln_notation=True)


def _lenient_expr(raw: str):
    """Trailing word tokens are dropped one by one until the text parses."""
    candidates = [_mathify(raw.strip()), raw.strip()]
    for text in candidates:
        expr = try_sympify(text)
        if expr is not None:
            return expr
    text = _mathify(raw.strip())
    while text:
        expr = try_sympify(text)
        if expr is not None:
            return expr
        tokens = text.split()
        if len(tokens) <= 1:
            return None
        text = " ".join(tokens[:-1])
    return None


def _function_of(question: str):
    """Sorudeki fonksiyonu ve değişkenini çıkarır; yoksa None."""
    candidates = []
    for match in re.finditer(r"(?:y|f)\s*\(\s*([a-z])\s*\)\s*=\s*([^,;.]+)", normalize(question)):
        candidates.append(match.group(1))
        candidates.append(match.group(2))
    for match in re.finditer(r"\by\s*=\s*([^,;.]+)", normalize(question)):
        candidates.append(match.group(1))
    for match in re.finditer(r"(?:^|,|;)\s*[fy]\s*=\s*([^,;.\[\]]+)", normalize(question)):
        candidates.append(match.group(1))
    interval_head = re.match(r"\s*([^,;\[\]]+?)\s*[\[(]\s*-?\d", normalize(question))
    if interval_head:
        candidates.append(interval_head.group(1))
    for raw in reversed(candidates):
        expr = _lenient_expr(raw)
        if expr is not None and expr.free_symbols:
            var = sorted(expr.free_symbols, key=lambda s: s.name)[0]
            if expr != var:
                return expr, var
    return None


class AdvancedAnalysisSolver(Solver):
    name = "advanced_analysis"
    title = "İleri Analiz"

    def can_handle(self, question: str) -> float:
        q = _norm(question)
        if re.search(r"d[oö]n[eé]l?|d[oö]ngel?", q) and re.search(r"hacim|hacmi", q):
            return 0.9 if self._volume_data(question) else 0.0
        parse = _function_of(question)
        if not parse:
            return 0.0
        if re.search(r"te[gğ]et|tangent", q):
            return 0.9
        if re.search(r"ekstremum|extremum|kritik nokta|max\s*ve\s*min\s*nokta", q):
            return 0.9
        if ((re.search(r"en\s+b[üu]y[üu]k|en\s+k[üu][cç][üu]k|maximum|minimum", q)
                or (re.search(r"\bmax\b", q) and re.search(r"\bmin\b", q)))
                and (_INTERVAL_RE.search(q) or re.search(r"aral[ıi][ğg]|interval", q))):
            return 0.98
        if re.search(r"meydan|alan|area|square", q):
            if re.search(r"ceklen|cekli|çaklen|çakli|çevrili|sinirlan|sinirli|ınırl|between|aras", q):
                return 0.9
            try:
                if self._area_data(question):
                    return 0.9
            except Exception:  # noqa: BLE001
                pass
        if re.search(r"d[oö]n[eé]l?|d[oö]ngel?", q) and re.search(r"hacim|hacmi", q):
            if self._volume_data(question):
                return 0.9
        return 0.0

    def solve(self, question: str) -> Solution:
        q = _norm(question)
        if re.search(r"d[oö]n[eé]l?|d[oö]ngel?", q) and re.search(r"hacim|hacmi", q):
            data = self._volume_data(question)
            if data:
                return self._solve_volume(question, data)
        if re.search(r"te[gğ]et|tangent", q):
            data = self._tangent_data(question)
            if data:
                return self._solve_tangent(question, data)
        if re.search(r"ekstremum|extremum|kritik nokta", q):
            data = self._extrema_data(question)
            if data:
                return self._solve_extrema(question, data)
        if ((re.search(r"en\s+b[üu]y[üu]k|en\s+k[üu][cç][üu]k|maximum|minimum", q)
                or (re.search(r"\bmax\b", q) and re.search(r"\bmin\b", q)))
                and (_INTERVAL_RE.search(q) or re.search(r"aral[ıi][ğg]|interval", q))):
            data = self._closed_interval_data(question)
            if data:
                return self._solve_closed_interval(question, data)
        if re.search(r"meydan|alan|area", q):
            data = self._area_data(question)
            if data:
                return self._solve_area(question, data)
        raise ValueError("İleri analiz alt problemi belirlenemedi.")

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

    # ------------------------------------------------------- teğet denklemi
    def _tangent_data(self, question: str):
        func = _function_of(question)
        if func is None:
            return None
        q = _norm(question)
        match = _POINT_RE.search(q)
        if not match:
            return None
        x0 = sp.Rational(match.group(1))
        expr, var = func
        return {"expr": expr, "var": var, "x0": x0}

    def _solve_tangent(self, question: str, data) -> Solution:
        steps: list[Step] = []
        expr, var, x0 = data["expr"], data["var"], data["x0"]
        steps.append(Step("Fonksiyon", content=expr, detail=f"değişken: {var.name}"))
        value0 = expr.subs(var, x0)
        steps.append(Step("Noktanın y'si", latex=rf"{_L(var)} = {_L(x0)} \Rightarrow f({_L(x0)}) = {_L(value0)}"))
        slope = sp.diff(expr, var)
        steps.append(Step("Türev (eğim fonksiyonu)", content=slope))
        slope_at = slope.subs(var, x0)
        steps.append(Step("Noktadaki eğim", latex=rf"f'({_L(x0)}) = {_L(simplify_safe(slope_at))}"))
        y_sym = sp.Symbol("y")
        line = sp.expand(slope_at * (sp.Symbol(var.name) - x0) + value0)
        var_named = sp.Symbol(var.name)
        steps.append(Step("Teğet denklemi",
                          latex=rf"y - {_L(value0)} = {_L(slope_at)}\left({var.name} - {_L(x0)}\right) \Rightarrow y = {_L(line)}"))
        result = sp.Eq(y_sym, line, evaluate=False)
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Teğet denklemi", data={
            "kind": "tangent", "expr": expr, "var": var, "x0": x0,
            "value0": value0, "slope": slope_at, "line": line,
        })

    # ------------------------------------------------------------- ekstremum
    def _extrema_data(self, question: str):
        func = _function_of(question)
        if func is None:
            return None
        return {"expr": func[0], "var": func[1]}

    def _solve_extrema(self, question: str, data) -> Solution:
        steps: list[Step] = []
        expr, var = data["expr"], data["var"]
        steps.append(Step("Fonksiyon", content=expr))
        f1 = sp.diff(expr, var)
        steps.append(Step("1. türev", content=f1))
        steps.append(Step("Kritik noktalar", detail=f"{var.name} = 0 hâline getirilir"))
        criticals = sp.solve(sp.Eq(f1, 0), var)
        if not criticals:
            raise ValueError("Kritik nokta bulunamadı.")
        steps.append(Step("f'(x) = 0 denkleminin kökleri",
                          latex=", ".join(rf"{var.name} = {_L(c)}" for c in criticals)))
        f2 = sp.diff(expr, var, 2)
        steps.append(Step("2. türev testi", content=f2,
                          detail="f''(c) < 0 → tepe (maksimum), f''(c) > 0 → çukur (minimum)"))
        results = []
        max_tex, min_tex = [], []
        for c in criticals:
            second_at = f2.subs(var, c)
            value = expr.subs(var, c)
            if second_at < 0:
                max_tex.append(rf"{var.name} = {_L(c)} \Rightarrow f = {_L(value)}")
            elif second_at > 0:
                min_tex.append(rf"{var.name} = {_L(c)} \Rightarrow f = {_L(value)}")
            else:
                steps.append(Step(f"{var.name} = {_L(c)} noktasında test belirsiz",
                                  detail="f''(c) = 0; işaret incelemesi gerekir"))
        if max_tex:
            steps.append(Step("Yerel maksimum(lar)", latex=r" \quad ".join(max_tex)))
        if min_tex:
            steps.append(Step("Yerel minimum(lar)", latex=r" \quad ".join(min_tex)))
        result = sp.simplify(expr.subs(var, criticals[0])) if len(criticals) == 1 else steps
        summary_tex = r" \quad ".join(max_tex + min_tex)
        class_task = []
        for c in criticals:
            second_at = f2.subs(var, c)
            if second_at < 0:
                class_task.append((c, "max"))
            elif second_at > 0:
                class_task.append((c, "min"))
        return self._solution(question, summary_tex, steps, "Ekstremum noktaları", data={
            "kind": "ekstremum", "expr": expr, "var": var,
            "criticals": criticals, "f1": f1, "f2": f2, "classes": class_task,
        })

    # ------------------------------------------------- kapalı aralıkta değerler
    def _closed_interval_data(self, question: str):
        func = _function_of(question)
        if func is None:
            return None
        match = _INTERVAL_RE.search(_norm(question))
        if not match:
            return None
        a, b = sp.Rational(match.group(1)), sp.Rational(match.group(2))
        a, b = (a, b) if a <= b else (b, a)
        return {"expr": func[0], "var": func[1], "a": a, "b": b}

    def _solve_closed_interval(self, question: str, data) -> Solution:
        steps: list[Step] = []
        expr, var, a, b = data["expr"], data["var"], data["a"], data["b"]
        steps.append(Step("Fonksiyon ve aralık",
                          latex=rf"f({_L(var)}) = {_L(expr)}, \quad {_L(var)} \in \left[{_L(a)}; {_L(b)}\right]"))
        f1 = sp.diff(expr, var)
        steps.append(Step("Türev", latex=rf"f'({_L(var)}) = {_L(f1)}"))
        criticals = []
        for root in sp.solve(sp.Eq(f1, 0), var):
            if root.is_real and a <= root <= b:
                criticals.append(root)
        if criticals:
            steps.append(Step("İç kritik noktalar",
                              latex=", ".join(rf"{var.name} = {_L(c)}" for c in criticals),
                              detail=f"f'({_L(var)}) = 0 köklerinden [{_L(a)}; {_L(b)}] içinde olanlar"))
        else:
            steps.append(Step("İç kritik nokta yok",
                              detail=f"f'({_L(var)}) = 0 kökleri aralıkta değil"))
        candidates = [*criticals, a, b]
        table_rows = []
        values = {}
        for c in candidates:
            value = sp.simplify(expr.subs(var, c))
            values[c] = value
            table_rows.append(rf"f({_L(c)}) = {_L(value)}")
        steps.append(Step("Değer tablosu", latex=r", \quad ".join(table_rows),
                          detail="kritik iç noktalar ve uç noktalar hep birlikte değerlendirilir"))
        max_c = max(values, key=lambda c: float(values[c].evalf()))
        min_c = min(values, key=lambda c: float(values[c].evalf()))
        steps.append(Step("Karşılaştırma",
                          latex=rf"\max = f({_L(max_c)}) = {_L(values[max_c])}, \quad \min = f({_L(min_c)}) = {_L(values[min_c])}"))
        result_tex = rf"\max f = {_L(values[max_c])}, \quad \min f = {_L(values[min_c])}"
        return self._solution(question, result_tex, steps, "Kapalı aralıkta en büyük/en küçük değer", data={
            "kind": "closed_interval", "expr": expr, "var": var,
            "a": a, "b": b, "f1": f1, "criticals": criticals, "values": values,
            "max_c": max_c, "min_c": min_c,
        })

    # --------------------------------------------------------- eğriler arası alan
    def _area_data(self, question: str):
        clause = _clean_area_text(question)
        symbolic_curves: list[tuple[sp.Expr, sp.Symbol]] = []
        constant_curves: list[sp.Expr] = []
        verticals: list[sp.Basic] = []
        for text in re.findall(r"[^,;.]+=[^,;.]+", clause):
            lhs, _, rhs = text.partition("=")
            left = _lenient_expr(lhs)
            right = _lenient_expr(rhs)
            if left is None or right is None:
                continue
            if left == sp.Symbol("y") or getattr(left, "name", "") == "y":
                if right.free_symbols:
                    if len(right.free_symbols) == 1:
                        var = sorted(right.free_symbols, key=lambda s: s.name)[0]
                        symbolic_curves.append((right.simplify(), var))
                elif right.is_number:
                    constant_curves.append(sp.sympify(right))
                continue
            if left == sp.Symbol("x") and right.is_number and not right.free_symbols:
                verticals.append(sp.sympify(right))
        if not symbolic_curves:
            return None
        var = symbolic_curves[0][1]
        curves = [curve for curve, curve_var in symbolic_curves if curve_var == var]
        curves.extend(constant_curves)
        if len(verticals) >= 2:
            a, b = sorted(verticals, key=lambda v: float(v.evalf()))[:2]
            if len(curves) == 1:
                curves.append(sp.Integer(0))
            if len(curves) < 2:
                return None
            return {"f": curves[0], "g": curves[1], "var": var, "a": a, "b": b,
                    "verticals": verticals}
        if len(curves) >= 2:
            return {"f": curves[0], "g": curves[1], "var": var, "a": None, "b": None,
                    "verticals": verticals}
        return None

    def _solve_area(self, question: str, data) -> Solution:
        steps: list[Step] = []
        f, g, var = data["f"], data["g"], data["var"]
        steps.append(Step("Eğriler", latex=rf"y = {_L(f)}, \quad y = {_L(g)}"))
        if data["a"] is None:
            intersections = [r for r in sp.solve(sp.Eq(f, g), var) if r.is_real]
            verticals = [v for v in data.get("verticals") or []]
            candidates = sorted(
                [r for r in intersections + verticals if sp.sympify(r).is_real],
                key=lambda r: float(r.evalf()))
            if len(intersections) >= 2:
                a, b = candidates[:2]
            elif len(candidates) >= 2:
                a, b = candidates[0], candidates[-1]
            else:
                raise ValueError("İki eğri arasında sınırlı kapalı bölge bulunamadı.")
            steps.append(Step("Sınır noktaları",
                              latex=rf"{_L(var)} = {_L(a)}, \; {_L(b)}"))
        else:
            a, b = data["a"], data["b"]
            steps.append(Step("Dik sınır doğruları",
                              latex=rf"{_L(var)} = {_L(a)}, \quad {_L(var)} = {_L(b)}"))
        mid = (a + b) / 2
        upper = f.subs(var, mid)
        lower = g.subs(var, mid)
        if float(upper.evalf()) < float(lower.evalf()):
            f, g = g, f
        diff = sp.expand(f - g)
        steps.append(Step("Alan formülü",
                          latex=rf"S = \int_{{ {_L(a)} }}^{{ {_L(b)} }} \left( {_L(f)} - {_L(g)} \right) d{_L(var.name)}"))
        antiderivative = sp.integrate(diff, var)
        steps.append(Step("Antitürev", content=antiderivative))
        upper_at = antiderivative.subs(var, b)
        lower_at = antiderivative.subs(var, a)
        steps.append(Step("Sınırları yerine koy",
                          latex=rf"\left[ {_L(antiderivative)} \right]_{{ {_L(a)} }}^{{ {_L(b)} }} = {_L(upper_at)} - ({_L(lower_at)})"))
        result = sp.integrate(diff, (var, a, b))
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Eğrilerle sınırlı alan", data={
            "kind": "area", "f": f, "g": g, "var": var, "a": a, "b": b,
            "diff": diff, "antiderivative": antiderivative,
        })


    # ------------------------------------------------------- dönel cisim hacmi
    def _volume_data(self, question: str):
        q = _norm(question)
        q = q.replace(",", " ")
        func = _function_of(question)
        if func is None:
            m = re.search(r"\b([a-z])\s*=\s*(.+?)\s+([a-z])\s*=\s*(-?\d+(?:/\d+)?)\s*\.\.\s*(-?\d+(?:/\d+)?)", q)
            if not m:
                m = re.search(r"\b([a-z])\s*=\s*(.+?)\s+([a-z])\s*=\s*(-?\d+)\s*dan?\s+(-?\d+)\s*[yae]\b", q)
            if not m or m.group(1) != m.group(3):
                return None
            expr = _lenient_expr(m.group(2))
            if expr is None or not expr.has(sp.Symbol(m.group(1))):
                return None
            func = (expr, sp.Symbol(m.group(1)))
        m = re.search(rf"\b{func[1].name}\s*=\s*(-?\d+)\s*(?:\.\.|dan|den)\s+(-?\d+)\s*(?:[yae]\b|\.\.)", q)
        if not m:
            m = re.search(rf"\b{func[1].name}\s*=\s*(-?\w+)\.\.\s*(-\w+|\w+)", q)
        if not m:
            m = re.search(r"\bfrom\s*(-?[\w.π/]+)\s+to\s*(-?[\w.π/]+)", q)
        if not m:
            return None
        lo, hi = None, None
        try:
            if ".." in m.group(0):
                lo = try_sympify(m.group(1))
                hi = try_sympify(m.group(2))
            else:
                lo = try_sympify(m.group(1))
                hi = try_sympify(m.group(2))
        except Exception:  # noqa: BLE001
            return None
        if lo is None or hi is None or not lo.is_number or not hi.is_number:
            return None
        if lo >= hi:
            lo, hi = hi, lo
        return {"expr": func[0], "var": func[1], "a": lo, "b": hi}

    def _solve_volume(self, question: str, data) -> Solution:
        steps: list[Step] = []
        expr, var, a, b = data["expr"], data["var"], data["a"], data["b"]
        steps.append(Step("Dönel hacim formülü",
                          latex=rf"V = \pi \int_{{ {_L(a)} }}^{{ {_L(b)} }} y^2 \, d{_L(var.name)}",
                          detail="eksen çevresinde dönen eğri silindirik dilim hacmi verir"))
        square = sp.expand(expr ** 2)
        steps.append(Step("Kare al", latex=rf"y^2 = \left({_L(expr)}\right)^2 = {_L(square)}"))
        antiderivative = sp.integrate(square, var)
        steps.append(Step("Antitürev", content=antiderivative))
        result = sp.pi * sp.integrate(square, (var, a, b))
        upper_at = sp.pi * antiderivative.subs(var, b)
        lower_at = sp.pi * antiderivative.subs(var, a)
        steps.append(Step("Sınırları yerine koy",
                          latex=rf"\pi \left[ {_L(antiderivative)} \right]_{{ {_L(a)} }}^{{ {_L(b)} }} = {_L(simplify_safe(upper_at))} - {_L(simplify_safe(lower_at))} = {_L(result)}"))
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Dönel cisim hacmi", data={
            "kind": "integral", "expr": square, "var": var,
            "bounds": (a, b), "result": result,
        })


def simplify_safe(expr):
    try:
        return sp.simplify(expr)
    except Exception:  # noqa: BLE001
        return expr


def _clean_area_text(question: str) -> str:
    text = normalize(question)
    text = re.sub(r"meydan\S*|alan\S*|area", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[a-züöçşiığ]*eklenen\w*|arasi", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\?", " ", text)
    text = re.sub(r"\bve\b|\band\b", ",", text, flags=re.IGNORECASE)
    return text
