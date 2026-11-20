"""İleri cebir çözücü: eşitsizlik, mutlak değer, logaritma/üstel ve kök
denklemleri, progressiya, Vieta, kalan teoremi, binom, karmaşık sayılar.

Her alt problem kendi defter tarzı adım zincirini üretir; sonuçlar her zaman
sympy ile hesaplanır. Kalıp tanınmazsa solver 0.0 döndürür ve motor sıradaki
çözücüyü dener.
"""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import fold_turkmen, normalize, try_sympify
from ..steps import linear_eq_steps
from .base import Solution, Solver, Step

_INEQ_RE = re.compile(r"<=|>=|≤|≥|<(?!=)|>(?![=>])")
_PIPES_RE = re.compile(r"\|([^|]+)\|")
_LOG_EQ_RE = re.compile(r"log_?\{?(\d+)\}?\s*\(([^()]+)\)\s*=\s*(.+)")
_LOG_TERM_RE = re.compile(r"(?P<sign>[+\-]?)\s*log_?\{?(\d+)\}?\s*\(([^()]+)\)")
_LOG_EVAL_RE = re.compile(r"([+\-]?)\s*log_?\{?(\d+)\}?\s*\(?\s*(-?\d+(?:\.\d+)?)\s*\)?")
_ASSIGN_RE = re.compile(r"([abqds])\s*_?\s*(\d*)\s*=\s*(-?\d+(?:\.\d+)?)")
_WANTED_RE = re.compile(r"([sb])\s*_?\s*(\d+)\s*=\s*\?")
_NTH_TERM_RE = re.compile(r"(\d+)\s*\.?\s*(?:terim|eleman|uyesi|üyesi|had)")
_TWO_SQUARE_RE = re.compile(r"([a-z])\s*\^\s*2\s*\+\s*([a-z])\s*\^\s*2")
_BINOM_RE = re.compile(r"\(([^()]+)\)\s*\^\s*(\d+)")
_COEFF_ASK_RE = re.compile(r"([a-z])\s*\^\s*(\d+)\s*[^,;]*?katsay", re.IGNORECASE)
_NOISE_EQ = r"\b(?:solve|denklemini|denklemi|denklem|equation|hesapla|hesaplay|madde|sorusu|coz|cozun|islevini)\b"


def _norm(question: str) -> str:
    return fold_turkmen(normalize(question)).lower()


def _clean_expr_text(question: str) -> str:
    text = normalize(question)
    text = re.sub(_NOISE_EQ, " ", text, flags=re.IGNORECASE)
    return re.sub(r"\?", " ", text).strip()


def _parse_single_equation(question: str):
    text = _clean_expr_text(question)
    if "=" not in text:
        return None
    lhs, _, rhs = text.partition("=")
    left, right = try_sympify(lhs), try_sympify(rhs)
    if left is None or right is None:
        return None
    symbols = (left.free_symbols | right.free_symbols) - {sp.Symbol("I")}
    if not symbols:
        return None
    var = sorted(symbols, key=lambda s: s.name)[0]
    return sp.Eq(left, right), var


def _L(expr) -> str:
    return sp.latex(expr, ln_notation=True)


_KEEP_ALPHA = {
    "sin", "cos", "tan", "cot", "sec", "csc", "exp", "ln", "log", "pi",
    "sqrt", "abs", "asin", "acos", "atan",
}


def _strip_words(text: str) -> str:
    """3+ harfli saf sozcukleri (kacadir, olsun, denkleminin...) temizler."""
    tokens = []
    for tok in text.split():
        core = tok.lower().lstrip("0123456789-")
        if len(core) >= 3 and core.isalpha() and core not in _KEEP_ALPHA:
            continue
        tokens.append(tok)
    return " ".join(tokens)


class AdvancedAlgebraSolver(Solver):
    name = "advanced_algebra"
    title = "İleri Cebir"

    # ------------------------------------------------------------ puanlama
    def can_handle(self, question: str) -> float:
        q = _norm(question)
        no_arrow = q.replace("->", " ").replace("=>", " ")
        has_ineq = _INEQ_RE.search(no_arrow)
        if "|" in q:
            if has_ineq and self._abs_ineq_data(question):
                return 0.92
            if self._abs_data(q) or self._modulus_data(question):
                return 0.85
        if has_ineq and self._ineq_data(question):
            return 0.95
        if self._multi_log_data(question):
            return 0.88
        if self._log_data(question) or self._log_eval_data(question):
            return 0.85
        if "=" not in q:
            if self._binomial_data(question) is not None:
                return 0.85
            if self._expand_data(question):
                return 0.85
        for detector, score in (
            (self._progression_data, 0.9),
            (self._vieta_data, 0.85),
            (self._sum_product_data, 0.85),
            (self._remainder_data, 0.85),
            (self._radical_data, 0.8),
            (self._exp_data, 0.8),
        ):
            if detector(question) is not None:
                return score
        if self._complex_only(q):
            return 0.95
        return 0.0

    def solve(self, question: str) -> Solution:
        q = _norm(question)
        if "|" in q:
            abs_ineq = self._abs_ineq_data(question)
            if abs_ineq:
                return self._solve_abs_ineq(question, abs_ineq)
            abs_data = self._abs_data(q)
            if abs_data:
                return self._solve_abs(question, abs_data)
            modulus = self._modulus_data(question)
            if modulus:
                return self._solve_modulus(question, modulus)
        multi_log = self._multi_log_data(question)
        if multi_log:
            return self._solve_multi_log(question, multi_log)
        log_data = self._log_data(question)
        if log_data:
            return self._solve_log_eq(question, log_data)
        log_eval = self._log_eval_data(question)
        if log_eval:
            return self._solve_log_eval(question, log_eval)
        ineq = self._ineq_data(question)
        if ineq:
            return self._solve_ineq(question, ineq)
        if "=" not in q:
            binom = self._binomial_data(question)
            if binom is not None:
                return self._solve_binomial(question, binom)
            expand = self._expand_data(question)
            if expand is not None:
                return self._solve_expand(question, expand)
        for detector, handler in (
            (self._progression_data, self._solve_progression),
            (self._vieta_data, self._solve_vieta),
            (self._sum_product_data, self._solve_sum_product),
            (self._remainder_data, self._solve_remainder),
            (self._binomial_data, self._solve_binomial),
            (self._radical_data, self._solve_radical),
            (self._exp_data, self._solve_exp),
        ):
            data = detector(question)
            if data is not None:
                return handler(question, data)
        if self._complex_only(q):
            return self._solve_complex_arithmetic(question)
        raise ValueError("İleri cebir alt problemi belirlenemedi.")

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

    # --------------------------------------------------------- eşitsizlikler
    def _ineq_data(self, question: str):
        q = _norm(question).replace("->", " ").replace("=>", " ")
        q = re.sub(r"\?", " ", q)
        match = _INEQ_RE.search(q)
        if not match:
            return None
        rel = match.group(0)
        lhs, rhs = q[:match.start()], q[match.end():]
        left, right = try_sympify(lhs), try_sympify(rhs)
        if left is None or right is None:
            return None
        symbols = left.free_symbols | right.free_symbols
        if not symbols:
            return None
        var = sorted(symbols, key=lambda s: s.name)[0]
        return {"expr": sp.expand(left - right), "rel": rel, "var": var}

    def _solve_ineq(self, question: str, data) -> Solution:
        steps: list[Step] = []
        expr, rel, var = data["expr"], data["rel"], data["var"]
        num, den = expr.as_numer_denom()
        sign_char = {"<": "<", "<=": "≤", ">": ">", ">=": "≥"}[rel]
        body = _L(sp.factor(num)) if den == 1 else rf"\frac{{ {_L(sp.factor(num))} }} {{ {_L(sp.factor(den))} }}"
        steps.append(Step("Tüm terimler bir tarafa", latex=rf"{body} \; {sign_char} \; 0"))
        criticals = []
        for part in (num, den):
            try:
                for root in sp.solve(sp.Eq(part, 0), var):
                    if root.is_real:
                        criticals.append(root)
            except Exception:  # noqa: BLE001
                continue
        criticals = sorted(set(criticals), key=lambda v: float(v.evalf()))
        denom_roots = [c for c in criticals if den.subs(var, c) == 0]
        if criticals:
            crit_tex = r", \quad ".join(rf"{_L(var)} = {_L(c)}" for c in criticals)
            detail = "payda kökleri çözüm kümesine girmez" if denom_roots else "ifadenin işaret değiştirdiği noktalar"
            steps.append(Step("Kritik noktalar", latex=crit_tex, detail=detail))
        else:
            steps.append(Step("Kritik nokta yok", detail="ifadenin işareti değişmez"))
        boundaries = [-sp.oo, *criticals, sp.oo]
        intervals_in: list = []
        sign_rows: list[str] = []
        for i in range(len(boundaries) - 1):
            a, b = boundaries[i], boundaries[i + 1]
            sample = self._sample(a, b)
            sign = self._sign(num * den, var, sample)
            left_label, right_label = self._interval_label(a, b)
            sign_rows.append(rf"{left_label} < {_L(var)} < {right_label}: {'+' if sign > 0 else ('-' if sign < 0 else '0')}")
            wanted = sign < 0 if rel in ("<", "<=") else sign > 0
            if wanted:
                if a == -sp.oo and b != sp.oo:
                    intervals_in.append(sp.Interval.open(-sp.oo, b))
                elif b == sp.oo and a != -sp.oo:
                    intervals_in.append(sp.Interval.open(a, sp.oo))
                elif a == -sp.oo and b == sp.oo:
                    intervals_in.append(sp.S.Reals)
                else:
                    intervals_in.append(sp.Interval.open(a, b))
        included_points = [c for c in criticals
                           if den.subs(var, c) != 0 and num.subs(var, c) == 0
                           and rel in ("<=", ">=")]
        answer_set = self._assemble_set(intervals_in, included_points)
        if denom_roots:
            steps.append(Step("Payda kökleri tanımsız",
                              latex=", ".join(rf"{_L(var)} \neq {_L(c)}" for c in denom_roots),
                              detail="0'a bölme olmadığı için bu noktalar çözüme girmez"))
        steps.append(Step("İşaret analizi", latex=r", \quad ".join(sign_rows)))
        if answer_set is sp.EmptySet:
            steps.append(Step("Çözüm yok",
                              latex="\\varnothing",
                              detail="ifade hiçbir aralıkta istenen koşulu sağlamıyor"))
        if included_points:
            steps.append(Step("Sınır noktaları dahil",
                              latex=r", \quad ".join(rf"{_L(var)} = {_L(c)}" for c in included_points),
                              detail=f"eşitlik ({sign_char} içindeki '=') durumunda sınır kökleri de çözümdür"))
        steps.append(Step("Çözüm kümesi", content=answer_set))
        return self._solution(question, answer_set, steps, "Eşitsizlik çözümü")

    @staticmethod
    def _sample(a, b):
        if a == -sp.oo:
            return b - 1 if b != sp.oo else sp.Integer(1)
        if b == sp.oo:
            return a + 1
        return sp.Rational(a + b) / 2

    @staticmethod
    def _sign(expr, var, sample):
        try:
            value = float(sp.N(expr.subs(var, sample)))
        except (TypeError, ValueError, ZeroDivisionError):
            return 0
        return 1 if value > 0 else (-1 if value < 0 else 0)

    @staticmethod
    def _interval_label(a, b):
        left = "-\\infty" if a == -sp.oo else _L(a)
        right = "+\\infty" if b == sp.oo else _L(b)
        return left, right

    @staticmethod
    def _assemble_set(intervals_in, included_points):
        if not intervals_in and not included_points:
            return sp.EmptySet
        if intervals_in and not included_points:
            return intervals_in[0] if len(intervals_in) == 1 else sp.Union(*intervals_in)
        pieces = list(intervals_in) + [sp.FiniteSet(c) for c in included_points]
        return pieces[0] if len(pieces) == 1 else sp.Union(*pieces)

    # ------------------------------------------------------------ mutlak değer
    def _abs_data(self, q: str):
        match = _PIPES_RE.search(q)
        if not match:
            return None
        after = q[match.end():]
        if "=" not in after:
            return None
        rhs = try_sympify(after.partition("=")[2])
        inner = try_sympify(match.group(1))
        if inner is None or rhs is None or not rhs.is_number:
            return None
        symbols = inner.free_symbols
        if not symbols:
            return None
        return {"inner": inner, "rhs": rhs, "var": sorted(symbols, key=lambda s: s.name)[0]}

    def _solve_abs(self, question: str, data) -> Solution:
        steps: list[Step] = []
        inner, rhs, var = data["inner"], data["rhs"], data["var"]
        if rhs < 0:
            steps.append(Step("Negatif mutlak değer",
                              latex=r"|A| = c,\; c < 0 \Rightarrow \varnothing"))
            steps.append(Step("Çözüm yok",
                              latex="\varnothing",
                              detail=f"{_L(sp.Abs(inner))} hiçbir zaman negatif olamaz"))
            return self._solution(question, sp.EmptySet, steps, "Mutlak değer denklemi")
        steps.append(Step("Mutlak değerin tanımı",
                          latex=rf"\left|{_L(inner)}\right| = {_L(rhs)} \Rightarrow {_L(inner)} = {_L(rhs)} \;\text{{veya}}\; {_L(inner)} = -({_L(rhs)})"))
        roots = []
        for idx, value in enumerate((rhs, -rhs), start=1):
            branch = sp.solve(sp.Eq(inner, value), var, dict=True)
            body = "; ".join(rf"{_L(sym)} = {_L(val)}" for sol in branch for sym, val in sol.items()) or r"\varnothing"
            steps.append(Step(f"Durum {idx}: {_L(inner)} = {_L(value)}", latex=body))
            roots.extend(sol[var] for sol in branch if var in sol)
        unique = sorted(set(roots), key=lambda v: float(sp.Abs(v.evalf())))
        if unique:
            checks = [
                rf"{_L(var)} = {_L(r)} \Rightarrow \left|{_L(inner.subs(var, r))}\right| = {_L(sp.Abs(inner.subs(var, r)))} \;\checkmark"
                for r in unique
            ]
            steps.append(Step("Kontrol", latex=r" \quad ".join(checks)))
        steps.append(Step("Çözüm kümesi", content=unique))
        return self._solution(question, unique, steps, "Mutlak değer denklemi")

    # ------------------------------------------------ mutlak değer eşitsizliği
    def _abs_ineq_data(self, question: str):
        clause = _norm(question)
        pipes = _PIPES_RE.search(clause)
        if not pipes:
            return None
        after = clause[pipes.end():]
        rel_match = re.match(r"\s*(>=|<=|>|<)", after)
        if not rel_match:
            return None
        rhs_text = _strip_words(re.sub(r"[?=,;]", " ", after[rel_match.end():])).strip()
        rhs = try_sympify(rhs_text)
        if rhs is None or not rhs.is_number:
            return None
        inner = try_sympify(pipes.group(1))
        if inner is None:
            return None
        symbols = inner.free_symbols
        if not symbols:
            return None
        var = sorted(symbols, key=lambda s: s.name)[0]
        return {"inner": inner, "rel": rel_match.group(1), "rhs": rhs, "var": var}

    def _solve_abs_ineq(self, question: str, data) -> Solution:
        steps: list[Step] = []
        inner, rel, rhs, var = data["inner"], data["rel"], data["rhs"], data["var"]
        c = sp.Abs(rhs)
        lt = rel in ("<", "<=")
        closed = rel in ("<=", ">=")
        steps.append(Step("Verilen eşitsizlik",
                          latex=rf"\left|{_L(inner)}\right| {rel} {_L(rhs)}"))
        if lt:
            steps.append(Step("Mutlak değer eşitsizliğinin tanımı",
                              latex=rf"|f| {{ {rel} }} c \\Leftrightarrow -c {{ {rel} }} f {{ {rel} }} c",
                              detail="mutlak değer c 'den küçükse içteki ifade −c ile c arasında kalmalıdır"))
            steps.append(Step("Çift eşitsizlik",
                              latex=rf"{_L(-c)} {{ {rel} }} {_L(inner)} {{ {rel} }} {_L(c)}"))
            result = sp.solve_univariate_inequality(
                (sp.Le if closed else sp.Lt)(sp.Abs(inner), c), var, relational=False)
            x1 = sp.solve(sp.Eq(inner, -c), var)
            x2 = sp.solve(sp.Eq(inner, c), var)
            if x1 and x2:
                steps.append(Step("Sınırlar",
                                  latex=rf"{_L(inner)} = ±{_L(c)} \\Rightarrow {_L(var)} = {_L(x1[0])}, \; {_L(x2[0])}"))
        else:
            steps.append(Step("Mutlak değer eşitsizliğinin tanımı",
                              latex=rf"|f| {{ {rel} }} c \\Leftrightarrow f {{ {rel} }} c \\;\\text{{veya}}\\; f {{ {rel} }} -c",
                              detail="mutlak değer c'yi aşar veya −c'nin altına inerse koşul sağlanır"))
            x1 = sp.solve(sp.Eq(inner, -c), var)
            x2 = sp.solve(sp.Eq(inner, c), var)
            if x1 and x2:
                eq_char = "\\leq" if closed else "<"
                steps.append(Step(f"Durum 1: {_L(inner)} {rel} {_L(c)}",
                                  latex=rf"{_L(inner)} {{ {rel} }} {_L(c)} \\Rightarrow {_L(var)} {{ {rel} }} {_L(x2[0])}"))
                steps.append(Step(f"Durum 2: {_L(inner)} {rel} -{_L(c)}",
                                  latex=rf"{_L(inner)} {{ {rel} }} -{_L(c)} \\Rightarrow {_L(var)} {{ {eq_char} }} {_L(x1[0])}"))
                steps.append(Step("Birleşim",
                                  detail="iki durumun aralıkları birleşim kümesi alınır"))
            result = sp.solve_univariate_inequality(
                (sp.Ge if closed else sp.Gt)(sp.Abs(inner), c), var, relational=False)
        steps.append(Step("Çözüm kümesi", content=result))
        return self._solution(question, result, steps, "Mutlak değer eşitsizliği")

    # ----------------------------------------------------------------- log
    def _multi_log_data(self, question: str):
        clause = _norm(question)
        terms = list(_LOG_TERM_RE.finditer(clause))
        if len(terms) < 2:
            return None
        eq_at = clause.find("=", terms[0].end())
        if eq_at < 0:
            return None
        rhs = try_sympify(_strip_words(clause[eq_at + 1:].strip()).strip("? "))
        if rhs is None or not rhs.is_number:
            return None
        base = int(terms[0].group(2))
        parsed: list[tuple[int, sp.Expr]] = []
        span_end = 0
        for t_idx, t in enumerate(terms):
            sign = -1 if t.group("sign") == "-" else 1
            arg = try_sympify(t.group(3))
            if arg is None or not arg.free_symbols or int(t.group(2)) != base:
                return None
            between = clause[span_end:t.start()].strip()
            if t_idx > 0 and between and not re.fullmatch(r"[+\-]*", between):
                return None
            span_end = t.end()
            parsed.append((sign, arg))
        leftovers = clause[span_end:eq_at].strip()
        if leftovers:
            return None
        return {"base": base, "terms": parsed, "rhs": rhs}

    def _solve_multi_log(self, question: str, data) -> Solution:
        steps: list[Step] = []
        base = sp.Integer(data["base"])
        terms, rhs = data["terms"], data["rhs"]
        sym = terms[0][1].free_symbols | terms[-1][1].free_symbols
        var = sorted(sym, key=lambda s: s.name)[0]
        product_terms = [arg if sign > 0 else 1 / arg for sign, arg in terms]
        product = sp.expand(sp.Mul(*product_terms))
        target = base ** rhs
        combined_tex = " + ".join(
            rf"\log_{{ {_L(base)} }}({_L(arg)})" if sign > 0
            else rf"- \log_{{ {_L(base)} }}({_L(arg)})" for sign, arg in terms)
        steps.append(Step("Logaritmanın toplam kuralı",
                          latex=rf"\log_{{ {_L(base)} }} f + \log_{{ {_L(base)} }} g = \log_{{ {_L(base)} }}(f \\cdot g)"))
        steps.append(Step("Tek logaritmada birleştir",
                          latex=rf"{combined_tex} = \log_{{ {_L(base)} }}({_L(product)}) = {_L(rhs)}"))
        steps.append(Step("Logaritmanın tanımı",
                          latex=rf"{_L(product)} = {_L(base)}^{{ {_L(rhs)} }} = {_L(target)}"))
        steps.append(Step("Standart biçim", latex=rf"{_L(sp.expand(product - target))} = 0"))
        results = sp.solve(sp.Eq(product, target), var, dict=True)
        valid = []
        for sol in results:
            if all(arg.subs(sol) > 0 for sign, arg in terms):
                valid.append(sol)
            else:
                steps.append(Step("Geçersiz kök elenir",
                                  latex=rf"{_L(var)} = {_L(sol.get(var))}",
                                  detail="her logaritmanın argümanı pozitif olmalıdır"))
        if valid:
            steps.append(Step("Çözüm",
                              latex="; ".join(rf"{_L(k)} = {_L(v)}" for k, v in valid[0].items())))
        else:
            steps.append(Step("Çözüm yok", latex="\\varnothing"))
        return self._solution(question, valid, steps, "Logaritmik denklem (çok terimli)")

    def _log_data(self, question: str):
        match = _LOG_EQ_RE.search(question)
        if not match:
            return None
        arg = try_sympify(_strip_words(match.group(2)))
        rhs = try_sympify(_strip_words(match.group(3).strip()))
        if arg is None or rhs is None or not arg.free_symbols:
            return None
        if not rhs.free_symbols and not rhs.is_number:
            return None
        return {"base": int(match.group(1)), "arg": arg, "rhs": rhs}

    def _solve_log_eq(self, question: str, data) -> Solution:
        steps: list[Step] = []
        base = sp.Integer(data["base"])
        arg, rhs = data["arg"], data["rhs"]
        var = sorted(arg.free_symbols, key=lambda s: s.name)[0]
        target = base**rhs
        steps.append(Step("Logaritmanın tanımı",
                          latex=rf"\log_{{ {_L(base)} }}({_L(arg)}) = {_L(rhs)} \Leftrightarrow {_L(arg)} = {_L(base)}^{{ {_L(rhs)} }}"))
        if rhs.free_symbols:
            steps.append(Step("Üstel biçime geç",
                              latex=rf"{_L(var)} = {_L(base)}^{{ {_L(rhs)} }}",
                              detail="her iki taraf üstel biçimde yazılır ve kökler hesaplanır"))
        elif target.is_number and rhs != 1:
            steps.append(Step("Sağ tarafın değeri",
                              latex=rf"{_L(base)}^{{ {_L(rhs)} }} = {_L(target)}"))
        results = sp.solve(sp.Eq(arg, target), var, dict=True)
        valid = []
        for sol in results:
            if arg.subs(sol) > 0:
                valid.append(sol)
            else:
                steps.append(Step("Geçersiz kök elenir",
                                  latex=rf"{_L(arg.subs(sol))} < 0",
                                  detail="logaritmanın argümanı pozitif olmalıdır"))
        if rhs.free_symbols and any(
            "LambertW" in str(sol.get(var, ""))
            for sol in valid
        ):
            steps.append(Step("Kapalı biçim LambertW veriyor",
                              latex="; ".join(rf"{_L(var)} = {_L(sol.get(var))}" for sol in valid),
                              detail="okul düzeyinde sayısal kökler daha okunaklıdır"))
            valid = [{var: root} for root in self._numeric_log_roots(arg - target, var)]
            steps.append(Step("Sayısal çözüm",
                              detail="kökler sayısal yöntemle bulunur",
                              latex=", ".join(rf"{_L(var)} \approx {_L(sp.N(r, 6))}" for r in
                                              (sol.get(var) for sol in valid))))
        if not valid:
            numeric = self._numeric_log_roots(arg - target, var)
            for root in numeric:
                valid.append({var: root})
            if numeric:
                steps.append(Step("Sayısal çözüm",
                                  detail="kapalı analitik biçim yok; kökler sayısal bulunur",
                                  latex=", ".join(rf"{_L(var)} \approx {_L(sp.N(r, 6))}" for r in numeric)))
        for sol in valid:
            steps.append(Step("Kök kontrolü",
                              latex=rf"{_L(arg.subs(sol))} > 0 \;\checkmark"))
        if valid:
            steps.append(Step("Çözüm",
                              latex="; ".join(rf"{_L(sym)} = {_L(val)}" for sol in valid for sym, val in sol.items())))
        return self._solution(question, valid, steps, "Logaritmik denklem")

    @staticmethod
    def _numeric_log_roots(expr, var):
        roots = []
        try:
            func = sp.lambdify(var, expr, "math")
            for guess in (0.05, 0.2, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 20.0):
                try:
                    root = sp.nsolve(expr, var, guess, tol=1e-14, maxsteps=60)
                except (ValueError, ZeroDivisionError, TypeError, RuntimeError):
                    continue
                root_val = float(root)
                if root_val <= 0:
                    continue
                if all(abs(root_val - float(r)) > 1e-8 for r in roots):
                    roots.append(root)
        except Exception:  # noqa: BLE001
            return []
        return roots

    def _log_eval_data(self, question: str):
        clause = _strip_words(normalize(question))
        matches = list(_LOG_EVAL_RE.finditer(clause))
        if not matches:
            return None
        remainder = _LOG_EVAL_RE.sub(" ", clause)
        if re.search(r"[a-zA-Z]", _strip_words(remainder)):
            return None
        terms = [
            {
                "sign": -1 if m.group(1) == "-" else 1,
                "base": int(m.group(2)),
                "arg": sp.Integer(m.group(3)),
            }
            for m in matches
        ]
        return {"terms": terms}

    def _solve_log_eval(self, question: str, data) -> Solution:
        steps: list[Step] = []
        parts: list[str] = []
        total = sp.Integer(0)
        for term in data["terms"]:
            value = sp.log(term["arg"], term["base"])
            total += term["sign"] * value
            steps.append(Step(
                rf"\log_{{ {_L(term['base'])} }}({_L(term['arg'])}) değeri",
                latex=rf"{_L(term['base'])}^{{ {_L(value)} }} = {_L(term['arg'])} \Rightarrow \log_{{ {_L(term['base'])} }}({_L(term['arg'])}) = {_L(value)}",
            ))
            parts.append(rf"{'+' if term['sign'] > 0 else '-'} {_L(value)}")
        steps.append(Step("Terimleri topla", latex=" ".join(parts).lstrip("+ ")))
        steps.append(Step("Sonuç", content=total))
        return self._solution(question, total, steps, "Logaritma değerlendirmesi")

    # ---------------------------------------------------------- progressiya
    def _progression_data(self, question: str):
        q = _norm(question)
        kind_word = bool(re.search(r"progressi|arifmetik|aritmetik|geometrik", q))
        values: dict = {}
        for match in _ASSIGN_RE.finditer(q):
            letter = match.group(1)
            key = letter + match.group(2)
            values[key] = sp.Rational(match.group(3))
            values[letter] = sp.Rational(match.group(3))
        wanted = _WANTED_RE.search(q)
        if wanted:
            wanted = (wanted.group(1), int(wanted.group(2)))
        else:
            nth = _NTH_TERM_RE.search(q)
            if nth:
                wanted = (None, int(nth.group(1)))
        if wanted is None:
            leftovers = _ASSIGN_RE.sub(" ", q)
            leftovers = re.sub(
                r"progressiya|progressi|arifmetik|aritmetik|geometrik|verilen|soru"
                r"|tapyn|tapy|tap|hesapla|icin|[?;,.=!]",
                " ", leftovers)
            fallback = re.search(r"\b([sabdq])\s*_?\s*(\d+)\b", leftovers)
            if fallback is None:
                return None
            wanted = (fallback.group(1).lower(), int(fallback.group(2)))
        if not kind_word and not values:
            return None
        if re.search(r"geometrik", q):
            kind = "geometric"
        elif re.search(r"arifmetik|aritmetik", q):
            kind = "arithmetic"
        else:
            kind = "geometric" if "q" in values or wanted[0] == "b" else "arithmetic"
        return {"kind": kind, "values": values, "wanted": wanted}

    def _solve_progression(self, question: str, data) -> Solution:
        steps: list[Step] = []
        kind, values, (letter, n) = data["kind"], data["values"], data["wanted"]
        if kind == "arithmetic":
            a1 = values.get("a1", values.get("a"))
            d = values.get("d")
            if a1 is None or d is None:
                raise ValueError("Arifmetik progressiýa için a1 ve d gerekli.")
            steps.append(Step("Verilenler", latex=rf"a_1 = {_L(a1)}, \quad d = {_L(d)}"))
            if letter == "s":
                steps.append(Step("Toplam formülü",
                                  latex=rf"S_{{ {n} }} = \frac{{2a_1 + (n-1)d}}{{2}} \cdot n"))
                inner = 2 * a1 + (n - 1) * d
                half = sp.simplify(inner / 2)
                steps.append(Step("Yerine koy",
                                  latex=rf"S_{{ {n} }} = \frac{{2 \cdot {_L(a1)} + {_L(n - 1)} \cdot {_L(d)}}}{{2}} \cdot {n} = \frac{{ {_L(inner)} }}{{2}} \cdot {n}"))
                steps.append(Step("Adım adım", latex=rf"S_{{ {n} }} = {_L(half)} \cdot {n}"))
                result = sp.simplify(half * n)
            else:
                result = sp.simplify(a1 + (n - 1) * d)
                steps.append(Step("n'inci terim formülü", latex=f"a_{{ {n} }} = a_1 + (n-1)d"))
                steps.append(Step("Yerine koy",
                                  latex=rf"a_{{ {n} }} = {_L(a1)} + {_L(n - 1)} \cdot {_L(d)} = {_L(result)}"))
        else:
            b1 = values.get("b1", values.get("b"))
            ratio = values.get("q")
            if b1 is None or ratio is None:
                raise ValueError("Geometrik progressiýa için b1 ve q gerekli.")
            steps.append(Step("Verilenler", latex=rf"b_1 = {_L(b1)}, \quad q = {_L(ratio)}"))
            if letter == "s":
                steps.append(Step("Toplam formülü (q ≠ 1)",
                                  latex=rf"S_{{ {n} }} = b_1 \cdot \frac{{q^{{ {n} }} - 1}}{{q - 1}}"))
                power = sp.simplify(ratio**n - 1)
                denom = sp.simplify(ratio - 1)
                result = sp.simplify(b1 * power / denom)
                steps.append(Step("Yerine koy",
                                  latex=rf"S_{{ {n} }} = {_L(b1)} \cdot \frac{{ {_L(ratio)}^{{ {n} }} - 1 }}{{ {_L(ratio)} - 1 }} = {_L(b1)} \cdot \frac{{ {_L(power)} }}{{ {_L(denom)} }} = {_L(result)}"))
            else:
                power = sp.simplify(ratio ** (n - 1))
                result = sp.simplify(b1 * power)
                steps.append(Step("n'inci terim formülü", latex=rf"b_{{ {n} }} = b_1 \cdot q^{{n-1}}"))
                steps.append(Step("Üssün değeri",
                                  latex=rf"q^{{ {n - 1} }} = {_L(ratio)}^{{ {n - 1} }} = {_L(power)}"))
                steps.append(Step("Yerine koy", latex=rf"b_{{ {n} }} = {_L(b1)} \cdot {_L(power)} = {_L(result)}"))
        steps.append(Step("Sonuç", content=result))
        label = "Arifmetik progressiýa" if kind == "arithmetic" else "Geometrik progressiýa"
        return self._solution(question, result, steps, label)

    # ----------------------------------------------------------------- vieta
    def _vieta_data(self, question: str):
        clause = _clean_expr_text(_norm(question))
        if "=" not in clause:
            return None
        has_kok = bool(re.search(r"k[oö]kleri", clause))
        has_icin = bool(re.search(r"\bicin\b", clause))
        if not has_kok and not has_icin:
            return None
        quad = None
        head = (re.split(r"k[o\xf6]kleri", clause)[0] if has_kok
                else re.split(r"\bicin\b", clause)[0])
        if "=" in head:
            lhs, _, rhs = head.partition("=")
            right = try_sympify(rhs.strip().split()[0] if rhs.strip().split() else "")
            left = try_sympify(lhs)
            if left is not None and right is not None:
                symbols = left.free_symbols | right.free_symbols
                if len(symbols) == 1:
                    var = sorted(symbols, key=lambda s: s.name)[0]
                    poly_expr = sp.expand(left - right)
                    try:
                        if sp.degree(poly_expr, var) == 2:
                            quad = (var, poly_expr)
                    except sp.PolynomialError:
                        pass
        if quad is None:
            return None
        tail = (re.split(r"k[oö]kleri", clause)[-1] if has_kok
                else re.split(r"\bicin\b", clause)[-1])
        target = None
        for part in reversed([p for p in re.split(r"[.;,]", tail) if p.strip()]):
            candidate = _strip_words(part.strip().rstrip("?="))
            candidate = re.sub(r"\s+", "", candidate.replace("x_1", "x1").replace("x_2", "x2"))
            expr = try_sympify(candidate)
            if expr is None:
                continue
            free = {s for s in expr.free_symbols if s.name.startswith("x")}
            if len(free) >= 2:
                target = expr
                break
        if target is None:
            return None
        return {"var": quad[0], "poly": quad[1], "target": target}

    def _solve_vieta(self, question: str, data) -> Solution:
        steps: list[Step] = []
        var, poly_expr, target = data["var"], data["poly"], data["target"]
        coeffs = sp.Poly(poly_expr, var).all_coeffs()
        a, b, c = (sp.Rational(v) for v in coeffs[:3])
        s = sp.simplify(-b / a)
        p = sp.simplify(c / a)
        steps.append(Step("Vieta teoremi",
                          latex=rf"x_1 + x_2 = -\frac{{b}}{{a}} = {_L(s)}, \quad x_1x_2 = \frac{{c}}{{a}} = {_L(p)}"))
        roots = sp.solve(sp.Eq(poly_expr, 0), var)
        x1 = x2 = None
        if len(roots) == 2:
            x1, x2 = sorted(roots, key=lambda r: float(sp.re(r.evalf())))
        target_value = None
        if x1 is not None and x2 is not None:
            syms = sorted(target.free_symbols, key=lambda sym: sym.name)
            if len(syms) == 2:
                target_value = sp.simplify(target.subs({syms[0]: x1, syms[1]: x2}))
        S, P = sp.Symbol("S"), sp.Symbol("P")
        formulas = (
            (r"x_1^{2} + x_2^{2}", S**2 - 2 * P,
             r"x_1^{2} + x_2^{2} = \left(x_1 + x_2\right)^2 - 2x_1x_2",
             lambda sv, pv, cv: rf"{formula_label} = {_L(sv)}^2 - 2 \cdot {_L(pv)} = {_L(sp.simplify(sv**2))} - {_L(2 * pv)} = {_L(cv)}"),
            (r"x_1^{3} + x_2^{3}", S**3 - 3 * P * S,
             r"x_1^{3} + x_2^{3} = \left(x_1 + x_2\right)^3 - 3x_1x_2\left(x_1 + x_2\right)",
             lambda sv, pv, cv: rf"{formula_label} = {_L(sv)}^3 - 3 \cdot {_L(pv)} \cdot {_L(sv)} = {_L(cv)}"),
            (r"\frac{1}{x_1} + \frac{1}{x_2}", S / P,
             r"\frac{1}{x_1} + \frac{1}{x_2} = \frac{x_1 + x_2}{x_1x_2}",
             lambda sv, pv, cv: rf"{formula_label} = \frac{{ {_L(sv)} }}{{ {_L(pv)} }} = {_L(cv)}"),
        )
        if target_value is not None:
            for formula_label, identity_expr, identity, numeric_latex in formulas:
                candidate = sp.simplify(identity_expr.subs({S: s, P: p}))
                if sp.simplify(candidate - target_value) == 0:
                    steps.append(Step("Özdeşlik", latex=identity))
                    steps.append(Step("Vieta değerlerini yerine koy",
                                      latex=numeric_latex(s, p, candidate)))
                    steps.append(Step("Sonuç", content=target_value))
                    return self._solution(question, target_value, steps, "Vieta uygulaması")
        if target_value is None:
            raise ValueError("Vieta hedefi çözülemedi.")
        steps.append(Step("Kökleri yerine koy",
                          latex=rf"x_1 = {_L(x1)}, \; x_2 = {_L(x2)}"))
        steps.append(Step("Sonuç", content=target_value))
        return self._solution(question, target_value, steps, "Vieta uygulaması")

    # ---------------------------------------------------------- a+b, ab verildi
    def _sum_product_data(self, question: str):
        clause = _norm(question)
        match = _TWO_SQUARE_RE.search(clause)
        if not match or "=" not in clause:
            return None
        equations = []
        for text in re.findall(r"[^,;.]+=[^,;.]+", _strip_words(clause)):
            text = re.sub(r"\bab\b", "a*b", text)
            text = re.sub(r"\bxy\b", "x*y", text)
            lhs, _, rhs = text.partition("=")
            first_token = rhs.strip().split()[:1]
            right = _strip_words(first_token[0]) if first_token else ""
            left, right = try_sympify(lhs), try_sympify(right)
            if left is not None and right is not None:
                equations.append(sp.Eq(left, right))
        sum_eq = prod_eq = None
        for eq in equations:
            free = eq.free_symbols
            if len(free) != 2:
                continue
            sym1, sym2 = sorted(free, key=lambda s: s.name)
            diff = sp.expand(eq.lhs - eq.rhs)
            try:
                poly = sp.Poly(diff, sym1, sym2)
            except sp.PolynomialError:
                continue
            monoms = [list(m) for m in poly.monoms()]
            if poly.total_degree() == 1 and [1, 0] in monoms and [0, 1] in monoms:
                sum_eq = eq
            elif poly.total_degree() == 2 and [1, 1] in monoms:
                prod_eq = eq
        if sum_eq is None or prod_eq is None:
            return None
        s_syms = sorted(sum_eq.free_symbols, key=lambda s: s.name)
        s_val = sum_eq.rhs if sum_eq.rhs.is_number else sum_eq.lhs
        p_val = prod_eq.rhs if prod_eq.rhs.is_number else prod_eq.lhs
        return {"sum_eq": sum_eq, "prod_eq": prod_eq,
                "sym1": s_syms[0], "sym2": s_syms[1], "s": s_val, "p": p_val}

    def _solve_sum_product(self, question: str, data) -> Solution:
        steps: list[Step] = []
        sym1, sym2 = data["sym1"], data["sym2"]
        s = sp.simplify(data["s"])
        p = sp.simplify(data["p"])
        steps.append(Step("Verilenler",
                          latex=rf"{_L(sym1)} + {_L(sym2)} = {_L(s)}, \quad {_L(sym1)}{_L(sym2)} = {_L(p)}"))
        steps.append(Step("Özdeşlik",
                          latex=rf"({_L(sym1)} + {_L(sym2)})^2 = {_L(sym1)}^2 + 2{_L(sym1)}{_L(sym2)} + {_L(sym2)}^2 \Rightarrow {_L(sym1)}^2 + {_L(sym2)}^2 = ({_L(sym1)} + {_L(sym2)})^2 - 2{_L(sym1)}{_L(sym2)}"))
        result = sp.simplify(s**2 - 2 * p)
        steps.append(Step("Yerine koy",
                          latex=rf"{_L(sym1)}^2 + {_L(sym2)}^2 = {_L(s)}^2 - 2 \cdot {_L(p)} = {_L(sp.simplify(s**2))} - {_L(2 * p)} = {_L(result)}"))
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Özdeşlik uygulaması")

    # ----------------------------------------------------------- kalan teoremi
    def _remainder_data(self, question: str):
        clause = _norm(question)
        if not re.search(r"kalan", clause) or not re.search(r"b[öo]l", clause):
            return None
        match = re.search(r"[pP]\s*\(\s*([a-z])\s*\)\s*=\s*([x^0-9+\-*/(). ]+)", clause)
        if match:
            var = sp.Symbol(match.group(1))
            poly = try_sympify(match.group(2).strip())
            if poly is None or not poly.is_polynomial(var):
                return None
            minus_div = re.search(r"x\s*-\s*(\d+(?:\.\d+)?)(?!\s*\^)", clause)
            plus_div = re.search(r"x\s*\+\s*(\d+(?:\.\d+)?)(?!\s*\^)", clause)
            if minus_div:
                c = sp.Rational(minus_div.group(1))
            elif plus_div:
                c = -sp.Rational(plus_div.group(1))
            else:
                return None
        else:
            poly_match = re.search(r"([x0-9^+\-*/(). ]+?)\s*polinomu\b", clause)
            div_match = re.search(r"\b([a-z])\s*([+-])\s*(\d+(?:\.\d+)?)\s+ile\s+b", clause)
            if not poly_match or not div_match:
                return None
            if div_match.group(1) != "x" and "x" not in poly_match.group(1):
                return None
            var = sp.Symbol(div_match.group(1))
            poly = try_sympify(poly_match.group(1).strip())
            if poly is None or not poly.is_polynomial(var):
                return None
            c = -sp.Rational(div_match.group(3)) if div_match.group(2) == "+" else sp.Rational(div_match.group(3))
        return {"var": var, "poly": poly, "c": c}

    def _solve_remainder(self, question: str, data) -> Solution:
        steps: list[Step] = []
        var, poly, c = data["var"], data["poly"], data["c"]
        result = sp.rem(sp.Poly(poly, var), sp.Poly(var - c, var)).as_expr()
        steps.append(Step("Kalan teoremi",
                          latex=rf"P(x) : ({_L(var)} - {_L(c)}) \text{{ ile bölünürse kalan }} = P({_L(c)})"))
        vals = [sp.together(t.subs(var, c)) for t in poly.as_ordered_terms()]
        signed = _L(vals[0])
        for v in vals[1:]:
            signed += f" + {_L(v)}" if v >= 0 else f" - {_L(-v)}"
        steps.append(Step("Yerine koy", latex=f"P({_L(c)}) = {signed} = {_L(result)}"))
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Kalan teoremi")

    # --------------------------------------------------------------- açılım
    def _expand_data(self, question: str):
        clause = _norm(question)
        if "=" in clause:
            return None
        match = _BINOM_RE.search(clause)
        if not match:
            return None
        if not re.search(r"\bac\b|ac[iı]l|acar|expand|ifadesin", clause):
            return None
        base = try_sympify(match.group(1))
        if base is None or len(base.free_symbols) != 1:
            return None
        n = int(match.group(2))
        if n <= 0 or n > 8:
            return None
        return {"base": base, "n": n}

    def _solve_expand(self, question: str, data) -> Solution:
        steps: list[Step] = []
        base, n = data["base"], data["n"]
        var = sorted(base.free_symbols, key=lambda s: s.name)[0]
        a, b = (base.as_ordered_terms() if base.is_Add else (base, sp.Integer(0)))
        if b == 0:
            a = base
            b = None
        steps.append(Step("Verilen ifade", content=base**n))
        steps.append(Step("Binom açılımı",
                          latex=rf"({ _L(a) } + { _L(b) if b is not None else 0 })^{{ {n} }} = \sum_{{k=0}}^{{ {n} }} \binom{{ {n} }}{{k}} \, { _L(a) }^{{ {n} -k}} { _L(b) }^{{k}}"))
        terms = []
        for k in range(n + 1):
            coeff = sp.binomial(n, k)
            term = sp.expand(coeff * a**(n - k) * (b**k if b is not None else 1) if b is not None else coeff * a**(n - k))
            terms.append(term)
        steps.append(Step("Terimler",
                          latex=" + ".join(_L(t) if not t.could_extract_minus_sign() else f"({_L(t)})" for t in terms)))
        result = sp.expand(base**n)
        steps.append(Step("Sadeleştirilmiş açılım", content=result))
        return self._solution(question, result, steps, "Binom açılımı")

    # ------------------------------------------------------------------ binom
    def _binomial_data(self, question: str):
        clause = _norm(question)
        if not re.search(r"katsay|coefficient|kars[ıi]l", clause):
            return None
        match = _BINOM_RE.search(clause)
        coeff_match = _COEFF_ASK_RE.search(clause)
        if not match or not coeff_match:
            return None
        base = try_sympify(match.group(1))
        if base is None:
            return None
        var_name = coeff_match.group(1)
        target = sp.Symbol(var_name)
        a, b = sp.expand(base).as_ordered_terms() if base.is_Add else (base, sp.Integer(1))
        if not a.has(target):
            a, b = b, a
        if not a.has(target):
            return None
        return {"a": a, "b": b, "n": int(match.group(2)), "k": int(coeff_match.group(2)), "var": var_name}

    def _solve_binomial(self, question: str, data) -> Solution:
        steps: list[Step] = []
        a, b, n, k = data["a"], data["b"], data["n"], data["k"]
        j = n - k
        binom = sp.binomial(n, j)
        b_power = sp.expand(b**j)
        steps.append(Step("Binom teoremi",
                          latex=r"(a+b)^{n} = \sum_{j=0}^{n} \binom{n}{j} a^{n-j} b^{j}"))
        steps.append(Step("İstenen terim",
                          latex=rf"\left({_L(a)} + {_L(b)}\right)^{{ {n} }} \text{{ açılımında }} {_L(sp.Symbol(data['var']))}^{{ {k} }} \text{{ terimi: }} j = {j}"))
        steps.append(Step("Katsayı hesabı",
                          latex=rf"\binom{{ {n} }}{{ {j} }} = {binom}, \quad \left({_L(b)}\right)^{{ {j} }} = {_L(b_power)}"))
        result = sp.expand((a + b) ** n).coeff(sp.Symbol(data["var"]), k)
        steps.append(Step("Çarpım", latex=rf"{binom} \cdot {_L(b_power)} = {_L(result)}"))
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Binom açılımı")

    # ------------------------------------------------------------ kök denklemi
    def _radical_data(self, question: str):
        parsed = _parse_single_equation(question)
        if parsed is None:
            return None
        eq, var = parsed
        sqrts = [a for a in sp.preorder_traversal(eq)
                 if isinstance(a, sp.Pow) and a.exp == sp.Rational(1, 2)]
        lhs_sq = [a for a in sp.preorder_traversal(eq.lhs)
                  if isinstance(a, sp.Pow) and a.exp == sp.Rational(1, 2)]
        if len(sqrts) != 1 or len(lhs_sq) != 1:
            return None
        return {"eq": eq, "var": var, "sqrt": sqrts[0]}

    def _solve_radical(self, question: str, data) -> Solution:
        steps: list[Step] = []
        eq, var, sq = data["eq"], data["var"], data["sqrt"]
        lhs, rhs = eq.lhs, eq.rhs
        steps.append(Step("Verilen denklem", content=eq))
        f = sq.args[0]
        steps.append(Step("İki tarafın karesi",
                          latex=rf"\left(\sqrt{{ {_L(f)} }}\right)^2 = \left({_L(rhs)}\right)^2 \Rightarrow {_L(f)} = {_L(sp.expand(rhs**2))}"))
        poly_expr = sp.expand(f - sp.expand(rhs**2))
        steps.append(Step("Standart biçim", latex=f"{_L(poly_expr)} = 0"))
        candidates = sp.solve(sp.Eq(poly_expr, 0), var)
        steps.append(Step("Denklemi çöz",
                          latex=", ".join(rf"{_L(var)} = {_L(root)}" for root in candidates)))
        roots = []
        checks = []
        for root in candidates:
            try:
                lhs_at = lhs.subs(var, root)
                rhs_at = rhs.subs(var, root)
                ok = sp.simplify(lhs_at - rhs_at) == 0
            except Exception:  # noqa: BLE001
                ok = False
            mark = r"\;\checkmark" if ok else r"\;\text{(eler)}"
            eq_char = "=" if ok else "\\neq"
            checks.append(rf"{_L(var)} = {_L(root)}: {_L(lhs_at)} {eq_char} {_L(rhs_at)} {mark}")
            if ok:
                roots.append(root)
        steps.append(Step("Kök denemesi",
                          latex=r" \quad ".join(checks),
                          detail="kare almak kök ekleyebilir; her aday orijinal denklemde denenir"))
        steps.append(Step("Geçerli kökler", content=roots))
        return self._solution(question, roots, steps, "Kök denklemi")

    # ----------------------------------------------------------- üstel denklem
    def _exp_data(self, question: str):
        parsed = _parse_single_equation(question)
        if parsed is None:
            return None
        eq, var = parsed
        exp_terms = [p for p in eq.atoms(sp.Pow) if p.exp.has(var) and p.base.is_number]
        if len(exp_terms) != 1 or not eq.rhs.is_number:
            return None
        base = exp_terms[0].base
        try:
            rhs_exp = sp.log(eq.rhs, base)
        except (ValueError, TypeError, ZeroDivisionError):
            return None
        if not rhs_exp.is_Integer:
            return None
        return {"eq": eq, "var": var, "base": base,
                "exp_lhs": exp_terms[0].exp, "exp_rhs": rhs_exp}

    def _solve_exp(self, question: str, data) -> Solution:
        steps: list[Step] = []
        eq, var, base = data["eq"], data["var"], data["base"]
        exp_lhs, exp_rhs = data["exp_lhs"], data["exp_rhs"]
        steps.append(Step("Verilen denklem", content=eq))
        steps.append(Step("Sağ tarafı aynı tabana yaz",
                          latex=rf"{_L(base ** exp_rhs)} = {_L(base)}^{{ {_L(exp_rhs)} }}"))
        steps.append(Step("Tabanlar eşitse üstler eşittir",
                          latex=rf"{_L(base)}^{{ {_L(sp.expand(exp_lhs))} }} = {_L(base)}^{{ {_L(exp_rhs)} }} \Rightarrow {_L(sp.expand(exp_lhs))} = {_L(sp.expand(exp_rhs))}"))
        lin_eq = sp.Eq(sp.expand(exp_lhs), sp.expand(exp_rhs))
        try:
            steps.extend(linear_eq_steps(lin_eq, var))
        except Exception:  # noqa: BLE001
            roots = sp.solve(lin_eq, var)
            steps.append(Step("Üst denklemi çöz",
                              latex="; ".join(rf"{_L(var)} = {_L(r)}" for r in roots)))
        results = sp.solve(eq, var, dict=True)
        real_results = [sol for sol in results if sol.get(var) is None or sol[var].is_real is not False]
        if len(real_results) != len(results):
            rejected = [sol.get(var) for sol in results if sol[var].is_real is False]
            steps.append(Step("Karmaşık kökler reddedilir",
                              latex=", ".join(rf"{_L(var)} = {_L(v)}" for v in rejected),
                              detail="okul düzeyinde yalnızca reel çözümler alınır"))
        return self._solution(question, real_results, steps, "Üstel denklem")

    # ----------------------------------------------------------- karmaşık sayı
    def _modulus_data(self, question: str):
        match = _PIPES_RE.search(question)
        if not match or "i" not in match.group(1).lower():
            return None
        value = try_sympify(match.group(1))
        if value is None or not value.has(sp.I) or value.free_symbols:
            return None
        return {"value": value}

    def _solve_modulus(self, question: str, data) -> Solution:
        steps: list[Step] = []
        value = data["value"]
        a, b = value.as_real_imag()
        result = sp.Abs(value)
        steps.append(Step("Modül formülü", latex=r"|a + bi| = \sqrt{a^2 + b^2}"))
        steps.append(Step("Yerine koy",
                          latex=rf"|{_L(value)}| = \sqrt{{ {_L(a)}^2 + {_L(b)}^2 }} = \sqrt{{ {_L(sp.expand(a**2 + b**2))} }}"))
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, "Karmaşık sayının modülü")

    def _complex_only(self, q: str) -> str | None:
        q = _norm(q).replace("?", "").rstrip("=").rstrip()
        if "=" in q or "|" in q:
            return None
        residue = re.sub(r"[\d+\-*/^().,\s]", "", q)
        if not residue or residue.replace("i", ""):
            return None
        return "i" in residue

    def _solve_complex_arithmetic(self, question: str) -> Solution:
        steps: list[Step] = []
        candidate = self._complex_only(question)
        if candidate is None:
            raise ValueError("İleri cebir alt problemi belirlenemedi.")
        text = normalize(question).replace("?", "").rstrip("=").rstrip()
        tokens = re.sub(r"[a-hj-zA-HJ-Z_]+", " ", text)
        expr = try_sympify(tokens)
        if expr is None or not isinstance(expr, sp.Expr) or not expr.has(sp.I):
            raise ValueError("İfade ayrıştırılamadı.")
        steps.append(Step("Verilen ifade", content=expr))
        expanded = sp.expand(expr)
        a, b = expanded.as_real_imag()
        steps.append(Step("Dağıt (i² = -1 kullan)",
                          latex=rf"{_L(expr)} = {_L(expanded)}"))
        steps.append(Step("Gerçek ve sanal kısım",
                          latex=rf"\text{{gerçek: }} {_L(a)}, \quad \text{{sanal: }} {_L(b)}"))
        steps.append(Step("Sonuç", content=expanded))
        return self._solution(question, expanded, steps, "Karmaşık sayı aritmetiği")
