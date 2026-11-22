"""Okul seviyesi ek soru aileleri: ters trigonometrik degerler, |f|=|g|,
tanim kumesi, ters fonksiyon, f(g(x)) kompozisyonu, artan/azalan araliklar,
donum noktalari ve polinom bolme (bolum + kalan).

Kural: kalip taninmazsa veya cozum kurulamazsa NoSolverFound / ValueError
yukseltir - sessiz cop uretmez. Her aile Solution.data icine dogrulanabilir
koyar; mathpad/verify.py bu veriyi bagimsiz kontrol eder.
"""

from __future__ import annotations

import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import fold_turkmen, normalize, try_sympify
from .base import NoSolverFound, Solution, Solver, Step


def _norm(question: str) -> str:
    return fold_turkmen(normalize(question)).lower()


def _L(expr) -> str:
    return sp.latex(expr, ln_notation=True)


_KEEP_WORDS = {"sin", "cos", "tan", "cot", "exp", "ln", "log", "pi", "sqrt",
               "abs", "oo", "asin", "acos", "atan", "arcsin", "arccos",
               "arctan", "arccot", "i", "e"}


def _strip_words(text: str) -> str:
    """Matematik parcasindan sonraki saf kelimeleri atar."""
    out = []
    for tok in text.strip().split():
        core = tok.strip(".,;:?")
        if core.isalpha() and len(core) >= 3 and core not in _KEEP_WORDS:
            break
        out.append(core)
    return " ".join(t for t in out if t)


def _mathified(question: str) -> str | None:
    """Anahtar kelimeleri atar; kuligi matematik parcasini döndürür."""
    tokens = []
    for tok in _norm(question).strip().split():
        core = tok.strip(".,;:?")
        if core.isalpha() and len(core) >= 3 and core not in _KEEP_WORDS:
            continue
        tokens.append(core)
    text = " ".join(t for t in tokens if t)
    return text or None


def _canonical_set(res):
    """Complement ve benzeri kumeleri Interval/Union bicimine cevirir."""
    res = sp.sympify(res)
    if isinstance(res, sp.Complement):
        a, b = res.args
        if a is sp.S.Reals:
            b = sp.simplify(b)
            points = list(b.args) if isinstance(b, sp.Union) else [b]
            parcalar = []
            for p in points:
                if isinstance(p, sp.FiniteSet) and len(p) == 1:
                    v = sp.sympify(next(iter(p)))
                    parcalar.extend([sp.Interval.open(-sp.oo, v), sp.Interval.open(v, sp.oo)])
                else:
                    return res
            return sp.Union(*parcalar)
    return res


class SchoolExtraSolver(Solver):
    name = "school_extra"
    title = "Okul Ekstra"

    def can_handle(self, question: str) -> float:
        q = _norm(question)
        if re.search(r"\b(asin|acos|atan|acot)\b", q):
            if re.search(r"d/dx|turev|onum|onu:|integral|limit|ikinji", q):
                return 0.0
            if self._inverse_trig_data(question):
                return 0.92
        if re.search(r"\|[^|]+\|\s*=\s*\|", q):
            if not re.search(r"<=|>=|<|>", q.replace("=", "")):
                if self._abs_abs_data(question):
                    return 0.92
        if re.search(r"tanim\s*kumesi|tanim\s*aralig|domain", q):
            if self._domain_data(question):
                return 0.92
        if re.search(r"ters\w*\s+fonks|ters\w*\s+funks|funks\w*\s+ters\w*|inverse", q):
            if not re.search(r"d/dx|turev|integral|turevini", q):
                if self._inverse_function_data(question):
                    return 0.92
        if re.search(r"\bf\s*\(\s*g\s*\(|\bg\s*\(\s*f\s*\(", q):
            if self._compose_data(question):
                return 0.92
        if re.search(r"artan|azalan|monoton|increasing|decreasing", q):
            if re.search(r"kumesi|aralik|interval|oldugu", q) and self._monotonic_data(question):
                return 0.92
        if re.search(r"donum\s*nokta|tepe\s*nokt|tepesi\b|parabol\w*\s+tepe|bukulma\s*nokta|inflection", q):
            if self._inflection_data(question):
                return 0.92
        if re.search(r"\bbol\b|b[oö]l", q) and not re.search(r"kalan", q):
            if self._division_data(question):
                return 0.92
        return 0.0

    def solve(self, question: str) -> Solution:
        q = _norm(question)
        if re.search(r"\b(asin|acos|atan|acot)\b", q) \
                and not re.search(r"d/dx|turev|onum|integral|limit|ikinji", q):
            data = self._inverse_trig_data(question)
            if data:
                return self._solve_inverse_trig(question, data)
        if re.search(r"\|[^|]+\|\s*=\s*\|", q) and not re.search(r"<=|>=|<|>", q.replace("=", "")):
            data = self._abs_abs_data(question)
            if data:
                return self._solve_abs_abs(question, data)
        if re.search(r"tanim\s*kumesi|tanim\s*aralig|domain", q):
            data = self._domain_data(question)
            if data:
                return self._solve_domain(question, data)
        if re.search(r"ters\w*\s+fonks|ters\w*\s+funks|funks\w*\s+ters\w*|inverse", q):
            data = self._inverse_function_data(question)
            if data:
                return self._solve_inverse_function(question, data)
        if re.search(r"\bf\s*\(\s*g\s*\(|\bg\s*\(\s*f\s*\(", q):
            data = self._compose_data(question)
            if data:
                return self._solve_compose(question, data)
        if re.search(r"artan|azalan|monoton|increasing|decreasing", q) and self._monotonic_data(question):
            data = self._monotonic_data(question)
            if data:
                return self._solve_monotonic(question, data)
        if re.search(r"donum\s*nokta|tepe\s*nokt|tepesi\b|parabol\w*\s+tepe|bukulma\s*nokta|inflection", q):
            data = self._inflection_data(question)
            if data:
                return self._solve_inflection(question, data)
        if re.search(r"\bbol\b|b[oö]l", q) and not re.search(r"kalan", q):
            data = self._division_data(question)
            if data:
                return self._solve_division(question, data)
        raise NoSolverFound(f"Okul ekstra kalibi anlasilamadi: {question!r}")

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

    # ------------------------------------------------- ters trigonometrik deger
    _INVERSE_FUNCS = {
        "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan, "arccot": sp.acot,
        "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "acot": sp.acot,
    }
    _PRINCIPAL = {
        "arcsin": (-sp.pi / 2, sp.pi / 2), "asin": (-sp.pi / 2, sp.pi / 2),
        "arccos": (0, sp.pi), "acos": (0, sp.pi),
        "arctan": (-sp.pi / 2, sp.pi / 2), "atan": (-sp.pi / 2, sp.pi / 2),
        "arccot": (0, sp.pi), "acot": (0, sp.pi),
    }

    @staticmethod
    def _balanced_arg(text: str) -> str | None:
        text = text.strip()
        if text.startswith("("):
            derinlik = 0
            for i, ch in enumerate(text):
                if ch == "(":
                    derinlik += 1
                elif ch == ")":
                    derinlik -= 1
                    if derinlik == 0:
                        return text[1:i].strip()
            return None
        tok = text.split()[0] if text.split() else ""
        return tok.strip(".,;:?") or None

    def _inverse_trig_data(self, question: str):
        raw = re.search(r"\b(asin|acos|atan|acot)\b\s*", _norm(question))
        if not raw:
            return None
        short = raw.group(1) if raw.group(1) in self._INVERSE_FUNCS else "arc" + raw.group(1)
        name = {"asin": "arcsin", "acos": "arccos", "atan": "arctan", "acot": "arccot"}.get(short, short)
        arg_text = self._balanced_arg(_norm(question)[raw.end():])
        if not arg_text:
            return None
        arg = try_sympify(arg_text)
        if arg is None or not arg.is_number:
            return None
        func = self._INVERSE_FUNCS.get(name)
        if func is None:
            return None
        try:
            angle = sp.simplify(func(arg))
        except Exception:  # noqa: BLE001
            return None
        if angle.has(sp.Float):
            angle = sp.nsimplify(angle)
        if not angle.is_number:
            return None
        return {"func": func, "func_name": name, "arg": arg, "angle": angle}

    def _solve_inverse_trig(self, question: str, data) -> Solution:
        steps = [Step("Deger", content=data["angle"])]
        return self._solution(question, data["angle"], steps, "Ters trigonometrik değer", data={
            "kind": "inverse_trig", "func": data["func"], "arg": data["arg"],
            "angle": data["angle"], "func_name": data["func_name"],
        })

    # ------------------------------------------------------------ |f| = |g|
    def _abs_abs_data(self, question: str):
        q = question.replace("\u2212", "-").replace("\u00b2", "^2").replace("\u2264", "<=").replace("\u2265", ">=")
        m = re.search(r"\|([^|]+)\|\s*=\s*\|([^|]+)\|", q)
        if not m:
            return None
        f = try_sympify(m.group(1).strip())
        g = try_sympify(m.group(2).strip())
        if f is None or g is None:
            return None
        symbols = f.free_symbols | g.free_symbols
        if len(symbols) != 1:
            return None
        var = next(iter(symbols))
        root_poly = sp.expand(f ** 2 - g ** 2)
        if not root_poly.is_polynomial(var):
            return None
        roots = [r for r in sp.solve(root_poly, var) if sp.im(r) == 0]
        return {"f": f, "g": g, "var": var, "roots": sorted(roots, key=lambda r: float(sp.N(r)))}

    def _solve_abs_abs(self, question: str, data) -> Solution:
        f, g, var, roots = data["f"], data["g"], data["var"], data["roots"]
        steps = [
            Step("Kare alma", latex=rf"{_L(f)}^2 = {_L(g)}^2"),
            Step("Denklem", content=sp.expand(f ** 2 - g ** 2)),
        ]
        result = [{var: r} for r in roots] or sp.S.EmptySet
        steps.append(Step("Sonuc", content=result))
        return self._solution(question, result, steps, "Mutlak değerli denklem |f|=|g|", data={
            "kind": "abs_abs", "f": f, "g": g, "var": var, "roots": roots,
        })

    # ------------------------------------------------------------ tanim kumesi
    def _domain_data(self, question: str):
        q = _norm(question)
        m = re.search(r"(?:tanim\s*kumesi|tanim\s*aralig\w*|domain\s*of|domain)\s*(.*)", q)
        rest = m.group(1) if m else q
        mm = re.match(r"\s*[a-z]\s*(?:\(\s*[a-z]\s*\))?\s*=\s*(.+)", rest)
        expr_text = mm.group(1) if mm else rest
        if not expr_text.strip():
            return None
        expr = try_sympify(expr_text.strip())
        if expr is None or not expr.free_symbols or len(expr.free_symbols) != 1:
            return None
        var = next(iter(expr.free_symbols))
        conds = []
        for node in sp.preorder_traversal(expr):
            if isinstance(node, sp.Pow) and isinstance(node.exp, sp.Rational):
                if node.exp == sp.Rational(1, 2):
                    conds.append(("kok", node.base))
                elif node.exp < 0:
                    conds.append(("payda", node.base))
            elif isinstance(node, sp.log):
                conds.append(("log", node.args[0]))
        return {"expr": expr, "var": var, "conds": conds}

    def _solve_domain(self, question: str, data) -> Solution:
        expr, var, conds = data["expr"], data["var"], data["conds"]
        steps = []
        if not conds:
            if not expr.is_polynomial(var) and not expr.is_rational_function(var):
                raise NoSolverFound(
                    f"Tanım kümesi kısıtı bulunamadı: {question!r}")
            domain = sp.S.Reals
        else:
            domain = sp.S.Reals
            for ad, arg in conds:
                if ad == "kok":
                    cond = arg >= 0
                elif ad == "log":
                    cond = arg > 0
                else:
                    cond = sp.Ne(arg, 0)
                parca = sp.solveset(cond, var, sp.S.Reals)
                domain = sp.Intersection(domain, parca)
                steps.append(Step("Kisit", latex=rf"{_L(cond)} \Rightarrow {_L(parca)}"))
        domain = _canonical_set(domain)
        steps.append(Step("Sonuc", content=domain))
        return self._solution(question, domain, steps, "Tanım kümesi", data={
            "kind": "domain", "expr": expr, "var": var, "res": domain,
        })

    # ------------------------------------------------------------ ters fonksiyon
    def _inverse_function_data(self, question: str):
        q = _norm(question)
        mm = re.search(r"[a-z]\s*(?:\(\s*([a-z])\s*\))?\s*=\s*([^,;]+)", q)
        if mm:
            expr = try_sympify(_strip_words(mm.group(2)))
        else:
            mt = _mathified(question)
            expr = try_sympify(mt) if mt else None
        if expr is None or len(expr.free_symbols) != 1:
            return None
        var = next(iter(expr.free_symbols))
        return {"expr": expr, "var": var}

    @staticmethod
    def _tersi_bul(expr, var, y):
        try:
            slv = sp.solveset(sp.Eq(expr, y), var, sp.S.Reals)
            if isinstance(slv, sp.Intersection):
                sets = [s for s in slv.args if isinstance(s, sp.FiniteSet)]
                if len(sets) != 1 or len(sets[0]) != 1:
                    return None
                return next(iter(sets[0]))
            if isinstance(slv, sp.FiniteSet) and len(slv) == 1:
                return next(iter(slv))
        except Exception:  # noqa: BLE001
            return None
        return None

    def _solve_inverse_function(self, question: str, data) -> Solution:
        expr, var = data["expr"], data["var"]
        y = sp.Symbol("y")
        inv = self._tersi_bul(expr, var, y)
        if inv is None:
            raise NoSolverFound(
                f"Fonksiyonun tersi yok veya tek bicimli degil (f({var.name}) = {expr}).")
        b, q_ = sp.Wild("b"), sp.Wild("q")
        m = inv.match(sp.sign(b) * sp.Abs(b) ** q_)
        if m and m[q_] == sp.Rational(1, 3):
            inv = sp.Pow(m[b], sp.Rational(1, 3), evaluate=False)
        else:
            inv = sp.simplify(inv)
        inv = inv.subs(y, var)
        steps = [
            Step("x = f^{-1}(y) cozuluyor", latex=rf"{_L(expr)} = y \Rightarrow x = {_L(inv)}"),
            Step("Degisken degistirme", content=inv),
        ]
        var_text = f"f^-1({var.name})"
        result = sp.Eq(sp.Symbol(var_text), inv, evaluate=False)
        steps.append(Step("Sonuc", content=result))
        return self._solution(question, result, steps, "Ters fonksiyon", data={
            "kind": "inverse_function", "expr": expr, "var": var, "inv": inv,
        })

    # ------------------------------------------------------------ f(g(x))
    def _compose_data(self, question: str):
        q = _norm(question)
        if not re.search(r"\bf\s*\(\s*g\s*\(|\bg\s*\(\s*f\s*\(", q):
            return None
        defs = {}
        outer = re.search(r"\b([a-z])\s*\(\s*([a-z])\s*\)", q)
        if not outer:
            return None
        for m in re.finditer(r"\b([fg])\s*\(\s*([a-z])\s*\)\s*=\s*([^,;]+)", q):
            name, var_name, expr_text = m.group(1), m.group(2), m.group(3)
            if "g(" in expr_text or "f(" in expr_text:
                continue
            expr = try_sympify(_strip_words(expr_text))
            if expr is None or len(expr.free_symbols) > 1:
                continue
            defs[name] = (expr, sp.Symbol(var_name))
        if "f" not in defs or "g" not in defs:
            return None
        fexpr, gexpr = defs["f"][0], defs["g"][0]
        gvar = defs["g"][1]
        comp = sp.expand(fexpr.subs(defs["f"][1], gexpr))
        return {"f": fexpr, "g": gexpr, "comp": comp, "var": gvar}

    def _solve_compose(self, question: str, data) -> Solution:
        comp, var = data["comp"], data["var"]
        steps = [
            Step("Bileske", latex=rf"f(g({_L(var)})) = {_L(data['f'])}"),
            Step("Yerleştirme", content=comp),
        ]
        result = comp
        steps.append(Step("Sonuc", content=result))
        return self._solution(question, result, steps, "Fonksiyon kompozisyonu", data={
            "kind": "composition", "f": data["f"], "g": data["g"],
            "comp": comp, "var": var,
        })

    # ------------------------------------------------------ artan/azalan aralik
    def _monotonic_data(self, question: str):
        clause = re.search(r"(?:artan|azalan)[^.]*", _norm(question))
        math_text = _mathified(question)
        if not math_text:
            return None
        expr = try_sympify(math_text)
        if expr is None or len(expr.free_symbols) != 1:
            return None
        var = next(iter(expr.free_symbols))
        if not expr.is_polynomial(var):
            return None
        f1 = sp.diff(expr, var)
        crits = sorted([r for r in sp.solve(f1, var) if r.is_number and sp.im(r) == 0],
                       key=lambda r: float(sp.N(r)))
        return {"expr": expr, "var": var, "f1": f1, "crits": crits}

    def _solve_monotonic(self, question: str, data) -> Solution:
        expr, var, f1, crits = data["expr"], data["var"], data["f1"], data["crits"]
        kenarlar = [-sp.oo, *crits, sp.oo]
        artan, azalan, pieces = [], [], []
        for i in range(len(kenarlar) - 1):
            a, b = kenarlar[i], kenarlar[i + 1]
            if a == sp.oo or b == -sp.oo:
                continue
            mid = (a + b) / 2 if (a != -sp.oo and b != sp.oo) else (b - 1 if b != sp.oo else a + 1)
            if not sp.simplify(mid).is_number:
                continue
            sign = complex(sp.N(f1.subs(var, mid))).real
            yon = "artan" if sign > 0 else "azalan"
            aralik = sp.Interval.open(a, b)
            pieces.append((a, b, yon))
            (artan if yon == "artan" else azalan).append(aralik)
        if not crits:
            raise NoSolverFound(f"f'({var.name}) = 0 kok vermedi, kritik nokta yok: {question!r}")
        steps = [
            Step("Turev", content=f1),
            Step("Kritik noktalar", content=crits),
        ]
        result = {"artan": sp.Union(*artan), "azalan": sp.Union(*azalan)}
        steps.append(Step("Sonuc", content=result))
        return self._solution(question, result, steps, "Artan/azalan aralıklar", data={
            "kind": "monotonicity", "var": var, "f1": f1,
            "crits": crits, "pieces": pieces,
        })

    # ------------------------------------------------------------ donum noktasi
    def _inflection_data(self, question: str):
        math_text = _mathified(question)
        if not math_text:
            return None
        math_text = re.sub(r"^[a-z]\s*=\s*", "", math_text)
        expr = try_sympify(math_text)
        if expr is None or len(expr.free_symbols) != 1:
            return None
        var = next(iter(expr.free_symbols))
        if not expr.is_polynomial(var):
            return None
        f2 = sp.diff(expr, var, 2)
        roots = sorted([r for r in sp.solve(f2, var) if r.is_number and sp.im(r) == 0],
                       key=lambda r: float(sp.N(r)))
        vertex = None
        try:
            poly = sp.Poly(expr, var)
        except sp.PolynomialError:
            poly = None
        if poly is not None and poly.degree() == 2:
            a, b, c = poly.all_coeffs()
            vx = -b / (2 * a)
            vertex = (sp.simplify(vx), sp.simplify(expr.subs(var, vx)), a)
        return {"expr": expr, "var": var, "f2": f2, "roots": roots, "vertex": vertex}

    def _solve_inflection(self, question: str, data) -> Solution:
        expr, var, f2, roots = data["expr"], data["var"], data["f2"], data["roots"]
        vertex = data.get("vertex")
        if vertex is not None:
            vx, vy, a = vertex
            kind = "minimum" if a > 0 else "maksimum"
            steps = [
                Step("Türev", latex=f"f'(x) = {to_latex(sp.diff(expr, var))}"),
                Step(
                    "Türevi sıfırla",
                    latex=rf"{to_latex(sp.diff(expr, var))} = 0 \Rightarrow {to_latex(var)} = {to_latex(vx)}",
                ),
                Step(
                    "İkinci türev testi",
                    latex=f"f''(x) = {to_latex(f2)} {'>' if a > 0 else '<'} 0 \\Rightarrow {kind}",
                ),
                Step(
                    "Tepe (dönüm) noktası",
                    latex=rf"\left({to_latex(vx)},\ {to_latex(vy)}\right)",
                    detail=f"parabolun {kind} noktasi",
                ),
            ]
            return self._solution(
                question, (vx, vy), steps,
                f"Tepe (dönüm) noktası",
                data={"kind": "vertex", "var": var.name, "x": vx, "y": vy})
        points = []
        for r in roots:
            eps = sp.Rational(1, 10)
            try:
                s1 = complex(sp.N(f2.subs(var, r - eps))).real
                s2 = complex(sp.N(f2.subs(var, r + eps))).real
            except Exception:  # noqa: BLE001
                continue
            if s1 * s2 < 0:
                points.append((r, expr.subs(var, r)))
        steps = [
            Step("Ikinci turev", content=f2),
            Step("f'' = 0 kokleri", content=roots),
            Step("Sonuc", content=points),
        ]
        return self._solution(question, points or sp.S.EmptySet, steps, "Dönüm noktası", data={
            "kind": "inflection", "var": var, "f2": f2, "points": points,
        })

    # ------------------------------------------------------------ polinom bolme
    def _division_data(self, question: str):
        q = _norm(question)
        head = re.sub(r"\s*ile\s+b[oö]l.*$", "", q)
        head = re.sub(r"^\s*b[oö]l\s*:?\s*", "", head)
        if not head:
            return None
        tokens = [t.strip(".,;:?") for t in head.split()]
        math_tokens = [t for t in tokens if t and not t.isalpha()]
        if len(math_tokens) != 2:
            return None
        p_text, d_text = math_tokens
        P = try_sympify(p_text)
        D = try_sympify(d_text)
        if P is None or D is None:
            return None
        symbols = P.free_symbols | D.free_symbols
        if len(symbols) != 1:
            return None
        var = next(iter(symbols))
        if not P.is_polynomial(var) or not D.is_polynomial(var):
            return None
        quotient, remainder = sp.div(P, D, var)
        return {"P": P, "D": D, "q": quotient, "r": remainder, "var": var}

    def _solve_division(self, question: str, data) -> Solution:
        P, D, quotient, remainder, var = data["P"], data["D"], data["q"], data["r"], data["var"]
        steps = [
            Step("Bolunen", content=P),
            Step("Bolen", content=D),
            Step("Bolum ve kalan", latex=rf"{_L(P)} = ({_L(D)})\cdot({_L(quotient)}) + {_L(remainder)}"),
        ]
        result = (quotient, remainder)
        steps.append(Step("Sonuc", content=result))
        return self._solution(question, result, steps, "Polinom bölme", data={
            "kind": "polynomial_division", "P": P, "D": D, "q": quotient,
            "r": remainder, "var": var,
        })
