"""Cebir çözücü: denklem sistemleri, çarpanlara ayırma, açma, basitleştirme."""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import fold_turkmen, normalize, try_sympify, try_sympify_lenient
from ..steps import linear_eq_steps
from .base import Solution, Solver, Step

_KW_STRONG = ("denklem", "coz", "solve", "equation", "kok", "carpan", "factor",
              "expand", "genislet", "simplify", "basitlest", "sadelest", "denlem")
_KW_WEAK = ("degisken", "bilinmeyen", "polinom", "polynomial")
_SPLIT = re.compile(r"[,;]|\bve\b|\band\b", flags=re.IGNORECASE)
_INEQ_RE = re.compile(r"<=|>=|<(?!=)|>(?![=>])")
_EQ_NOISE = r"\b(?:solve|çöz|çözün|coz|denklemini|denklemi|denklem|sistemi|equation|equations|" \
            r"köklerini|kökleri|bul|nedir|kaçtır|root|roots|denlem\S*|denlemani)\b"
_FX_NOISE = r"\b(?:factor\S*|[çc]arpanlar?\S*|factorize|expand|[gğ]enişlet|[gğ]enislet|çyzyklary|" \
            r"simplify|basitleştir\S*|basitleş\S*|sadeleş\S*|sadeleştir\S*|" \
            r"basitlestir\S*|basitlest\S*|sadelest\S*|baslashtir\S*|" \
            r"ifadesini|ifadeyi|ifade|expression|ay[iı]r\S*|boluji|bolumu)\b"
_SUFFIXES = ("'nin", "'nın", "'nun", "'ün", "'ın", "'in", "'yi", "'yı", "'si", "'i", "'ı")


def _clean(text: str) -> str:
    text = normalize(text)
    for suffix in _SUFFIXES:
        text = text.replace(suffix, " ")
    return text


def _extract_equations(text: str) -> list[sp.Eq]:
    cleaned = re.sub(_EQ_NOISE, " ", _clean(text), flags=re.IGNORECASE)
    cleaned = cleaned.replace(":", " ")
    equations: list[sp.Eq] = []
    for part in _SPLIT.split(cleaned):
        part = part.strip()
        if "=" not in part:
            continue
        lhs, _, rhs = part.partition("=")
        left, right = try_sympify_lenient(lhs), try_sympify_lenient(rhs)
        if left is None or right is None:
            continue
        try:
            equations.append(sp.Eq(left, right, evaluate=False))
        except (sp.SympifyError, TypeError, ValueError):
            continue
    return equations


_INDEXED_SYMBOL = re.compile(r"^[a-z]_?\d{0,2}$")

_REL_FUNCS = {
    "<": sp.StrictLessThan,
    "<=": sp.LessThan,
    ">": sp.StrictGreaterThan,
    ">=": sp.GreaterThan,
}

_RANGE_RE = re.compile(
    r"[\[(]\s*(-?[\w./]+)\s*[;,]\s*(-?[\w./]+)\s*[\])]",
    re.IGNORECASE,
)


def _extract_inequalities(text: str) -> list[sp.Relational]:
    """'x^2-4=0 ve x>0' gibi sorulardaki esitsizlik kosullarini okur."""
    cleaned = re.sub(_EQ_NOISE, " ", _clean(text), flags=re.IGNORECASE)
    cleaned = cleaned.replace(":", " ")
    conditions: list[sp.Relational] = []
    for part in _SPLIT.split(cleaned):
        part = part.strip(" .?!")
        if "=" in part or not part:
            continue
        match = _INEQ_RE.search(part)
        if not match:
            continue
        left = try_sympify(part[:match.start()])
        right = try_sympify(part[match.end():])
        if left is None or right is None:
            continue
        conditions.append(_REL_FUNCS[match.group(0)](left, right))
    return conditions


def _condition_holds(condition: sp.Relational, solution: dict) -> bool:
    mapping = {s: val for s, val in solution.items() if s in condition.free_symbols}
    if not mapping:
        return True
    try:
        evaluated = condition.subs(mapping)
    except Exception:  # noqa: BLE001
        return True
    from sympy.logic.boolalg import BooleanAtom
    if isinstance(evaluated, BooleanAtom):
        return bool(evaluated)
    return True


def _unknown_symbol(question: str) -> str | None:
    try:
        equations = _extract_equations(question)
    except Exception:  # noqa: BLE001
        return None
    for eq in equations:
        for expr in (eq.lhs, eq.rhs):
            for sym in expr.free_symbols:
                name = sym.name
                if len(name) < 3 or _INDEXED_SYMBOL.fullmatch(name):
                    continue
                if name in {"pi", "oo", "zoo", "inf"}:
                    continue
                return name
    return None


class AlgebraSolver(Solver):
    name = "algebra"
    title = "Cebir"

    _OTHER_DOMAIN = re.compile(
        r"t\u00fcrev|turev|derivative|d/dx|integral|limit|hosylay|onumi|\u00f6n\u00fcmi"
        r"|te[gğ]et|tangent|ekstremum|extremum|meydan|alan|area|differensial|diferens"
        r"|hacim|hacmi|donel|donu|donm|donul"
    )

    def can_handle(self, question: str) -> float:
        q = fold_turkmen(question).lower()
        if self._OTHER_DOMAIN.search(q):
            return 0.0
        if _unknown_symbol(question):
            return 0.0
        if "=" in q:
            if _extract_equations(question):
                score = 0.75
                if re.search(r"\bfactor|carpan|expand|basitlest|simplify", q):
                    score = 0.9
                return score
            return 0.0
        if self._is_transform_request(question):
            return 0.9
        return self._score(q, strong=_KW_STRONG, weak=_KW_WEAK)

    def solve(self, question: str) -> Solution:
        unknown = _unknown_symbol(question)
        if unknown:
            raise ValueError(
                f"Soruda tanınmayan '{unknown}' sembolü var; soru anlaşılamadı.")
        if self._is_transform_request(question):
            return self._transform(question)
        return self._solve_equations(question)


    def _is_transform_request(self, question: str) -> bool:
        return bool(re.search(r"\bfactor|carpan|expand|genislet|simplify|basitlest|sadelest", fold_turkmen(question).lower()))

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

    def _transform(self, question: str) -> Solution:
        steps: list[Step] = []
        q = fold_turkmen(question).lower()
        cleaned = re.sub(_FX_NOISE, " ", _clean(question), flags=re.IGNORECASE)
        expr = try_sympify(cleaned)
        if expr is None:
            raise ValueError("İfade ayrıştırılamadı.")
        steps.append(Step("Verilen ifade", content=expr))
        if re.search(r"\bfactor|carpan", q):
            result = sp.factor(expr)
            steps.append(Step("Çarpanlara ayırma", content=result))
            label = "Çarpanlara ayırma"
        elif re.search(r"\bexpand|genislet", q):
            result = sp.expand(expr)
            steps.append(Step("Parantezleri açma (expand)", content=result))
            label = "İfadeyi açma"
        else:
            result = sp.simplify(expr) if expr.free_symbols else sp.simplify(expr)
            steps.append(Step("Basitleştirme", content=result))
            label = "Basitleştirme"
        return self._solution(question, result, steps, label)

    def _solve_equations(self, question: str) -> Solution:
        steps: list[Step] = []
        conditions = _extract_inequalities(question)
        equations = _extract_equations(question)
        if not equations:
            raise ValueError("Denklem bulunamadı; '=' içeren bir ifade bekleniyordu.")

        symbols = sorted({sym for eq in equations for sym in eq.free_symbols}, key=lambda s: s.name)
        if not symbols:
            symbols = [sp.Symbol("x")]

        eq_tex = " \\quad;\\quad ".join(to_latex(eq) for eq in equations)
        steps.append(Step("Denklemler", latex=eq_tex))

        main_var = symbols[0]
        poly_expr = equations[0].lhs - equations[0].rhs
        is_quadratic = False
        try:
            poly = sp.Poly(poly_expr, main_var)
            is_quadratic = poly.degree() == 2 and len(symbols) == 1
        except sp.PolynomialError:
            pass

        if is_quadratic:
            a, b, c = poly.all_coeffs()
            delta = sp.simplify(b**2 - 4 * a * c)
            steps.append(Step("Standard biçim", latex=f"{to_latex(sp.expand(poly_expr))} = 0"))
            steps.append(Step(
                "Katsayılar",
                latex=f"a = {to_latex(a)}, \\quad b = {to_latex(b)}, \\quad c = {to_latex(c)}",
            ))
            steps.append(Step(
                "Diskriminant formülü",
                latex=f"\\Delta = b^2 - 4ac = \\left({to_latex(b)}\\right)^2 - 4 \\cdot {to_latex(a)} \\cdot {to_latex(c)} = {to_latex(delta)}",
            ))
            if delta > 0:
                note = "\\Delta > 0 \\Rightarrow \\text{iki farklı gerçek kök}"
            elif delta == 0:
                note = "\\Delta = 0 \\Rightarrow \\text{çift katlı tek kök}"
            else:
                note = "\\Delta < 0 \\Rightarrow \\text{gerçek kök yok, karmaşık kökler var}"
            steps.append(Step("Yorum", latex=note))
            if delta >= 0:
                root_a = (-b + sp.sqrt(delta)) / (2 * a)
                root_b = (-b - sp.sqrt(delta)) / (2 * a)
                steps.append(Step(
                    "Kök formülü",
                    latex=f"x_{{1,2}} = \\frac{{-b \\pm \\sqrt{{\\Delta}}}}{{2a}} = \\frac{{{to_latex(-b)} \\pm \\sqrt{{{to_latex(delta)}}}}}{{{to_latex(2 * a)}}} \\Rightarrow x_1 = {to_latex(root_a)}, \\; x_2 = {to_latex(root_b)}",
                ))

        if not is_quadratic and len(equations) == 1 and len(symbols) == 1:
            try:
                poly_lin = sp.Poly(poly_expr, main_var)
                if poly_lin.degree() == 1:
                    steps.extend(linear_eq_steps(equations[0], main_var))
            except sp.PolynomialError:
                pass

        results = sp.solve(equations, symbols, dict=True)
        results = self._apply_interval_roots(equations, symbols, results, steps, question)
        if conditions:
            cond_tex = r", \quad ".join(to_latex(c) for c in conditions)
            steps.append(Step("Koşullar", latex=cond_tex))
            results = [sol for sol in results if all(_condition_holds(c, sol) for c in conditions)]
        if is_quadratic and results and all(
            all(v.is_real and v.is_number for v in sol.values()) for sol in results
        ):
            results = sorted(
                results,
                key=lambda sol: sp.default_sort_key(-list(sol.values())[0]),
            )
        eq_data = {
            "kind": "equations",
            "equations": equations,
            "conditions": conditions,
            "results": results,
        }
        if len(equations) == 1 and results:
            self._append_trig_periodicity(steps, equations[0], symbols[0], results)
        if not results:
            steps.append(Step("Sonuç", latex="\\varnothing"))
            return self._solution(
                question, "∅ (gerçek sayılarda çözüm yok)", steps,
                "Denklem çözümü (çözüm yok)", data=eq_data)

        solution = results[0] if len(results) == 1 else results
        steps.append(Step("Çözüm kümesi", content=solution))
        return self._solution(
            question, results, steps, "Denklem çözümü", data=eq_data)

    @staticmethod
    def _apply_interval_roots(equations, symbols, results, steps, question):
        """'cos(2x)=0 [0;2pi]' yazımlarında aralıktaki TÜM kökleri döndürür."""
        bounds = None
        for match in _RANGE_RE.finditer(question):
            lo = try_sympify(match.group(1))
            hi = try_sympify(match.group(2))
            if lo is not None and hi is not None and lo.is_number and hi.is_number and lo < hi:
                bounds = match
                break
        if bounds is None or len(symbols) != 1 or len(equations) != 1:
            return results
        if not equations[0].atoms(sp.sin, sp.cos, sp.tan, sp.cot):
            return results
        try:
            in_range = sp.solveset(
                equations[0], symbols[0], domain=sp.Interval(lo, hi))
        except Exception:  # noqa: BLE001
            return results
        if not isinstance(in_range, sp.FiniteSet) or not in_range:
            return results
        ordered = sorted(in_range, key=sp.default_sort_key)
        steps.append(Step(
            f"{to_latex(lo)} ≤ {to_latex(symbols[0])} ≤ {to_latex(hi)} aralığındaki kökler",
            latex=r", \quad ".join(to_latex(v) for v in ordered),
            detail="verilen aralık içindeki tüm kökler listelenir",
        ))
        return [{symbols[0]: value} for value in ordered]

    @staticmethod
    def _append_trig_periodicity(steps, equation, var, results) -> None:
        body = equation.lhs - equation.rhs
        has_tan = bool(body.atoms(sp.tan, sp.cot))
        has_cos = bool(body.atoms(sp.cos))
        has_sin = bool(body.atoms(sp.sin))
        if not (has_tan or has_cos or has_sin):
            return
        branches: list[str] = []
        for sol in results:
            val = sol.get(var)
            if val is None:
                return
            if has_tan:
                branches.append(rf"{to_latex(var)} = {to_latex(val)} + k\pi")
            elif has_cos:
                branches.append(rf"{to_latex(var)} = \pm {to_latex(val)} + 2k\pi")
            else:
                branches.append(rf"{to_latex(var)} = {to_latex(val)} + 2k\pi")
                branches.append(rf"{to_latex(var)} = -{to_latex(val)} + 2k\pi")
        steps.append(Step(
            "Genel çözüm (periyodiklik)",
            latex=r" \quad ".join(branches) + r", \quad k \in \mathbb{Z}",
            detail="trigonometrik denklemin sonsuz sayıda çözümü vardır; ana çözüm periyot katlarıyla tekrarlanır",
        ))
