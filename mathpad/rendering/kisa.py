"""Kisa zincir (defter) yazicisi: yapisal sonuclarin dogrudan Unicode defteri.

Kaynak: cozucunun uretip dogrulayicidan gecen Solution. Burada yalnizca sunum
yapilir; yeniden cozum uretilmez. Cikista ham LaTeX komutu olamaz.
"""

from __future__ import annotations

import re

import sympy as sp

from ..utils import try_sympify

_SUB = str.maketrans("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋")
_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
_SUP_LETTER = {"e": "ᵉ", "x": "ˣ", "n": "ⁿ", "k": "ᵏ", "i": "ⁱ", "a": "ᵃ"}

MINUS = "\u2212"

_ATOMS = {sp.I: "i", sp.E: "e", sp.pi: "π", sp.oo: "∞"}  # golden: i, e, π


_NUM_RE = re.compile(r"^-?[0-9]+$")


def _neg(text: str) -> str:
    return text.replace("-", MINUS)


def _sup(text: str) -> str:
    text = _neg(text)
    if _NUM_RE.match(text):
        return text.translate(_SUP)
    letters = [_SUP_LETTER.get(ch) for ch in text]
    if text and all(letters):
        return "".join(letters)
    return "^(" + text + ")"


_IDX_RE = re.compile(r"^-?\d+(?:,\d+)*$")


def _sub(text: str) -> str:
    text = _neg(text).replace(MINUS, "-")
    if _IDX_RE.match(text):
        return text.translate(_SUB)
    return "_(" + text + ")"


def _num(v) -> str:
    v = sp.sympify(v)
    if v.is_Integer:
        return _neg(str(int(v)))
    return _neg(f"{v.p}/{v.q}")


def _coeff_prefix(coeff) -> tuple[str, str]:
    """(isaret, mutlak on-ek) — int sayi birlesik, rasyonel parantezli."""
    if coeff == 1:
        return "", ""
    if coeff.is_Integer:
        abs_text = str(int(abs(coeff)))
        return (MINUS if coeff < 0 else ""), abs_text
    abs_text = "(" + _num(abs(coeff)) + ")"
    return (MINUS if coeff < 0 else ""), abs_text


_TRIG = {sp.sin: "sin", sp.cos: "cos", sp.tan: "tan", sp.cot: "cot",
         sp.sec: "sec", sp.csc: "csc",
         sp.asin: "arcsin", sp.acos: "arccos", sp.atan: "arctan", sp.acot: "arccot"}


def nb(expr) -> str:
    """sympy ifadesini defter-unicode dizgesine cevirir."""
    expr = sp.sympify(expr)
    if isinstance(expr, sp.Integer):
        return _num(expr)
    if isinstance(expr, sp.Rational):
        return _num(expr)
    if expr.is_Atom:
        if expr in _ATOMS:
            return _ATOMS[expr]
        if isinstance(expr, sp.Symbol):
            return expr.name
        if expr.is_number:
            return _num(expr)
        return str(expr)
    if isinstance(expr, (sp.Add,)):
        return _add_text(expr)
    if isinstance(expr, sp.Mul):
        return _mul_text(expr)
    if isinstance(expr, sp.Pow):
        return _pow_text(expr)
    if isinstance(expr, sp.log):
        arg = expr.args[0]
        if isinstance(arg, sp.Symbol) or (arg.is_number and arg.is_Integer and arg > 0):
            return "ln " + nb(arg)
        return "ln(" + nb(arg) + ")"
    if isinstance(expr, sp.exp):
        arg = expr.args[0]
        if isinstance(arg, sp.Symbol) or (isinstance(arg, sp.Mul) and arg.as_coeff_Mul()[1].is_Symbol):
            return _exp_text(arg)
        if arg.is_Integer and 2 <= int(arg) <= 9:
            return "e" + _sup(str(int(arg)))
        return "e^(" + nb(arg) + ")"
    if type(expr) in _TRIG:
        name = _TRIG[type(expr)]
        arg = expr.args[0]
        if arg.is_Symbol:
            return f"{name} {nb(arg)}"
        if isinstance(arg, sp.Mul):
            coeff, rest = arg.as_coeff_Mul()
            if coeff.is_number and isinstance(rest, sp.Symbol):
                return f"{name} {_num(coeff)}{nb(rest)}"
        return f"{name}({nb(arg)})"
    if isinstance(expr, sp.Abs):
        return "|" + nb(expr.args[0]) + "|"
    if isinstance(expr, sp.Eq):
        return f"{nb(expr.lhs)} = {nb(expr.rhs)}"
    if expr.is_Atom:
        if expr in _ATOMS:
            return _ATOMS[expr]
        if isinstance(expr, sp.Symbol):
            return expr.name
        if expr.is_number:
            return _num(expr)
        return str(expr)
    from .latex import to_latex
    from .latextounicode import latex_to_unicode
    return latex_to_unicode(to_latex(expr)).replace("\\", "")


def _exp_text(arg) -> str:
    if isinstance(arg, sp.Symbol):
        return "e" + _sup(arg.name)
    coeff, rest = arg.as_coeff_Mul()
    if coeff == 1:
        return "e" + _sup(rest.name)
    return "e^(" + nb(arg) + ")"


def _special_atoms(t) -> bool:
    try:
        return bool(t.atoms(sp.exp, sp.log, sp.sin, sp.cos, sp.tan, sp.cot, sp.sec,
                            sp.csc, sp.pi, sp.E, sp.I, sp.oo)) or t.has(sp.exp)
    except Exception:
        return False


def _add_text(expr: sp.Add) -> str:
    def _frac_first(t):
        _, r = t.as_coeff_Mul()
        if isinstance(r, sp.Pow) and isinstance(r.exp, sp.Rational) and r.exp < 0:
            return 0
        if isinstance(r, sp.Mul) and any(
            isinstance(f, sp.Pow) and isinstance(f.exp, sp.Rational) and f.exp < 0
            for f in r.as_ordered_factors()
        ):
            return 0
        return 1

    def _const_last(t):
        if t.is_number:
            return 0 if False else (1 if (not t.free_symbols and not _special_atoms(t)) else 0)
        return 0

    terms = sorted(expr.as_ordered_terms(), key=lambda t: (_frac_first(t), _const_last(t)))
    if terms and terms[0].as_coeff_Mul()[0] < 0:
        for i, t in enumerate(terms):
            if t.is_number and not _special_atoms(t):
                if t > 0:
                    terms = [t] + terms[:i] + terms[i + 1:]
                break
    out = ""
    for i, term in enumerate(terms):
        coeff, rest = term.as_coeff_Mul()
        body = _body_wo_sign(coeff, rest)
        if i == 0:
            out = (MINUS + body) if coeff < 0 else body
        else:
            out += (" " + MINUS + " " + body) if coeff < 0 else (" + " + body)
    return out


def _body_wo_sign(coeff, rest) -> str:
    """negatif olmayan katsayi * kalan -> on-ekli metin."""
    if coeff == 1:
        return _rest_text(rest)
    if rest == 1:
        return _coeff_prefix(coeff * (-1) if coeff < 0 else coeff)[1] or "1"
    return nb(sp.Mul(-coeff if coeff < 0 else coeff, rest))


def _rest_text(rest) -> str:
    if isinstance(rest, sp.Add):
        return "(" + nb(rest) + ")"
    return nb(rest)


def _pi_scalar(coeff) -> str:
    sign = MINUS if coeff < 0 else ""
    c = abs(coeff)
    if c == 1:
        return sign + "\u03c0"
    if c.is_Integer:
        return sign + str(int(c)) + "\u03c0"
    num_text = "" if c.p == 1 else str(c.p)
    return f"{sign}{num_text}\u03c0/{c.q}"


def _imag_scalar(coeff) -> str:
    sign = MINUS if coeff < 0 else ""
    c = abs(coeff)
    if c == 1:
        return sign + "i"
    if c.is_Integer:
        return sign + str(int(c)) + "i"
    num_text = "" if c.p == 1 else str(c.p)
    return f"{sign}{num_text}i/{c.q}"


def _mul_text(expr_sp: sp.Mul) -> str:
    coeff, rest = expr_sp.as_coeff_Mul()
    if coeff == 0:
        return "0"
    others, recips = [], []
    for f in rest.as_ordered_factors():
        if f == 1:
            continue
        if isinstance(f, sp.Pow) and isinstance(f.exp, sp.Rational) and f.exp < 0:
            recips.append(sp.Pow(f.base, -f.exp))
        else:
            others.append(f)
    if not others and not recips:
        return _num(expr_sp)
    if len(others) == 1 and not recips and others[0] == sp.pi:
        return _pi_scalar(coeff)
    if len(others) == 1 and not recips and others[0] == sp.I:
        return _imag_scalar(coeff)
    sign, prefix = _coeff_prefix(coeff)
    core = ""
    prefix_match = re.fullmatch(r"\(1/(\d+)\)", prefix or "")
    if (len(others) == 1 and not recips and prefix_match
            and isinstance(others[0], sp.Pow) and isinstance(others[0].base, sp.Add)
            and others[0].exp.is_Integer):
        return sign + nb(others[0]) + "/" + prefix_match.group(1)
    for i, f in enumerate(others):
        if i and not core.endswith(")"):
            core += " "
        core += _factor_text(f)
    if (len(recips) == 1 and len(others) == 1 and isinstance(others[0], sp.Pow)
            and isinstance(others[0].base, sp.Add) and others[0].exp.is_Integer
            and recips[0].is_Integer and prefix == "(1/" + _num(recips[0]) + ")"):
        return sign + nb(others[0]) + "/" + _num(recips[0])
    if recips:
        rec_vals = [sp.simplify(r) for r in recips]
        den = _denom_text(rec_vals[0]) if len(rec_vals) == 1 else _denom_text(sp.Mul(*rec_vals))
        numerator = (prefix + core) if core else (prefix or "1")
        return sign + numerator + "/" + den
    text = (prefix + core) if (prefix and core) else (core or prefix or "1")
    return sign + text if sign else text


def _denom_text(v) -> str:
    if isinstance(v, sp.Add):
        return "(" + nb(v) + ")"
    text = nb(v)
    if getattr(v, "is_Atom", False):
        return text
    if text.startswith("(") and _fully_parenthesized(text):
        return text
    if text.startswith("√"):
        return text
    if isinstance(v, sp.Mul) or " " in text or MINUS in text:
        return "(" + text + ")"
    return text


_SUP_CHARS = set("⁰¹²³⁴⁵⁶⁷⁸⁹⁻ᵉˣⁿᵏⁱ")


def _fully_parenthesized(text: str) -> bool:
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and i < len(text) - 1:
            return all(c in _SUP_CHARS for c in text[i + 1:])
    return depth == 0


def _factor_text(factor) -> str:
    if isinstance(factor, sp.Add):
        return "(" + nb(factor) + ")"
    text = nb(factor)
    if text.startswith(MINUS) or text.endswith(MINUS):
        return "(" + text + ")"
    return text


def _pow_text(expr: sp.Pow) -> str:
    base, exp = expr.base, expr.exp
    if isinstance(base, sp.exp):
        inner = base.args[0] * exp
        if isinstance(inner, sp.Symbol):
            return "e" + _sup(inner.name)
        return "e^(" + nb(inner) + ")"
    if exp == sp.Rational(1, 2):
        return _sqrt_text(base)
    if exp == sp.Rational(1, 3):
        return "\u221b(" + nb(base) + ")" if not base.is_Symbol else "\u221b" + nb(base)
    if exp.is_Rational and exp < 0:
        den = sp.Pow(base, -exp)
        num = "1"
        return num + "/" + _denom_text(den)
    if isinstance(base, sp.Symbol):
        if exp.is_Integer and 2 <= int(exp) <= 9:
            return base.name + _sup(str(int(exp)))
        if exp.is_Rational and exp > 0:
            return base.name + "^(" + _num(exp) + ")"
        return base.name + _sup(_num(exp))
    body = nb(base)
    if isinstance(base, (sp.Add, sp.Mul)):
        body = "(" + body + ")"
    if isinstance(base, sp.Pow) and MINUS in body:
        body = "(" + body + ")"
    if exp.is_Integer and 2 <= int(exp) <= 9:
        return body + _sup(str(int(exp)))
    if exp.is_Rational and exp > 0:
        return body + "^(" + _num(exp) + ")"
    return body + _sup(_num(exp))


def _sqrt_text(base) -> str:
    if base.is_Symbol:
        return "√" + nb(base)
    inner = nb(base)
    compact = re.fullmatch(r"-?\d+", inner.replace(" ", "")) or inner.isalnum()
    if compact:
        return "√" + inner.replace(" ", "")
    return "√(" + inner + ")"


def _sup_hi(hi: str) -> str:
    if hi == "e":
        return "ᵉ"
    if hi == "x":
        return "ˣ"
    if hi in ("π", "2π"):
        return "^" + hi
    if "/" in hi:
        return "^(" + hi + ")"
    return _sup(hi)


def _bound_text(v) -> str:
    v = sp.sympify(v)
    if v == sp.oo:
        return "∞"
    if v == sp.pi:
        return "π"
    if v == sp.E:
        return "e"
    if isinstance(v, sp.Mul):
        coeff, rest = v.as_coeff_Mul()
        if rest == sp.pi:
            if coeff.is_Integer:
                return _neg(str(int(coeff))) + "π"
            if isinstance(coeff, sp.Rational) and coeff.p == 1:
                return "π/" + str(coeff.q)
        if rest == sp.E:
            return nb(v).replace(" ", "")
    return nb(v).replace(" ", "")


def sinirlar(lo, hi) -> str:
    """Sikisik sinir yazimi: ₀¹, ₋₁¹, ₁ᵉ, ₀^π..."""
    lo_text = _bound_text(lo)
    hi_text = _bound_text(hi)
    return _sub(lo_text) + _sup_hi(hi_text)


def kume_yaz(res) -> str:
    """Sympy kume/aralik nesnesini defter-unicode yazimina cevirir."""
    if isinstance(res, str):
        return res
    if res == sp.S.EmptySet:
        return "\u2205"
    if res == sp.S.Reals:
        return "ℝ"
    if isinstance(res, sp.Interval):
        return _interval_yaz(res)
    if isinstance(res, sp.Union):
        parcalar = [p for p in res.args if isinstance(p, (sp.Interval, sp.FiniteSet))]
        return " ∪ ".join(kume_yaz(p) for p in parcalar)
    if isinstance(res, sp.FiniteSet):
        return _koked_yaz(list(res))
    from .latex import to_latex
    from .latextounicode import latex_to_unicode
    return latex_to_unicode(to_latex(res)).replace("\\", "")


def _interval_yaz(aralik: sp.Interval) -> str:
    def edge(v):
        if v == sp.oo:
            return "+∞"
        if v == -sp.oo:
            return MINUS + "∞"
        return _num(v)

    left = "[" if not aralik.left_open else "("
    right = "]" if not aralik.right_open else ")"
    return f"{left}{edge(aralik.start)}; {edge(aralik.end)}{right}"


def _koked_yaz(values, symbol_name: str = "x") -> str:
    parts = ", ".join(f"{symbol_name} = {_num(v)}" for v in values)
    return parts


# ======================================================================
# Aile kurucular: cozucunun yapisal verisinden defter-kisa zinciri.
# Yalnizca sunum; yeniden cozum uretilmez (sonuclar dogrulanmis gelir).
# ======================================================================

_PRIME = "\u2032"
_DOUBLE_PRIME = "\u2033"

_REL_U = {"<": "<", ">": ">", "<=": "\u2264", ">=": "\u2265", "=": "="}


def _signed_join(texts):
    """Birinci eleman oldugu gibi, sonraki elemanlar +/− ile birlestirilir."""
    out = ""
    for i, t in enumerate(texts):
        t = t.strip()
        if not t:
            continue
        neg = t.startswith(MINUS)
        body = t[1:].lstrip() if neg else t
        if i == 0:
            out = (MINUS + body) if neg else body
        else:
            out += (" " + MINUS + " " + body) if neg else (" + " + body)
    return out


def _poly_terms(expr, var):
    """Terimleri degiskenin derecesine gore ARTAN siraya dizer."""
    expr = sp.expand(expr)
    if not isinstance(expr, sp.Add):
        return [expr]
    def deg(t):
        try:
            return int(sp.degree(sp.Poly(t, var)))
        except Exception:
            if t.has(var):
                return 1
            return 0
    return sorted(sp.Add.make_args(expr), key=deg)


def _mono_monomial(rest, var) -> bool:
    if rest.is_Symbol:
        return True
    return (isinstance(rest, sp.Pow) and rest.base.is_Symbol
            and getattr(rest.exp, "is_Integer", False))


def _mono_term(coeff, rest, var) -> str | None:
    """p/q katsayili monom: p==1 -> X^k/q sonek, digerleri None (on-ek)."""
    if not (isinstance(coeff, sp.Rational) and coeff.q != 1):
        return None
    if not _mono_monomial(rest, var):
        return None
    if coeff.p not in (1, -1):
        return None
    return nb(rest) + "/" + str(coeff.q)


def _asc_text(expr, var) -> str:
    """Antiturevler icin terimleri degiskenin derecesine gore ARTAN yaz."""
    parts = _poly_terms(expr, var)
    texts = []
    for t in parts:
        coeff, rest = t.as_coeff_Mul()
        mono = _mono_term(coeff, rest, var)
        if mono is not None:
            body = mono
        elif coeff == 1:
            body = _rest_text(rest) if rest != 1 else "1"
        else:
            body = _body_wo_sign(abs(coeff) if coeff < 0 else coeff, rest)
        texts.append(MINUS + body if coeff < 0 else body)
    return _signed_join(texts)


def _micro_parse(question: str):
    """Soru metnini ifadelere acar; anlasilamazsa (None, None, None)."""
    text = question.replace("\u2212", "-").replace("\u2264", "<=").replace("\u2265", ">=")
    text = text.replace("\u00b2", "^2").replace("\u00b3", "^3")
    for token in ("sadelestir", "sadele\u015ftir", "\u00e7arpanlar\u0131na ay\u0131r", "\u00e7arpanlara ayir",
                  "\u00e7\u00f6z", "solve", "nedir", "hesapla", "bul", "open", "\u00e7arpanlara ayir"):
        text = re.sub(re.escape(token), " ", text, flags=re.IGNORECASE)
    match = re.search(r"\s*(<=|>=|=|<|>)\s*", text)
    if not match:
        return None, None, None
    lhs_raw = text[:match.start()].strip()
    rel = match.group(1)
    rhs_raw = text[match.end():].strip()
    lhs, rhs = try_sympify(lhs_raw), try_sympify(rhs_raw)
    if lhs is None or rhs is None:
        return None, None, None
    return lhs, _REL_U[rel], rhs


def _single_var(symbols):
    names = sorted(s.name for s in symbols)
    if not names:
        return None, None
    if len(names) > 1:
        return None, None
    return sp.Symbol(names[0]), names[0]


def _complex_text(z) -> str:
    z = sp.sympify(z)
    re_p, im_p = sp.re(z), sp.im(z)
    if im_p == 1:
        im_text = "i"
    elif im_p == -1:
        im_text = "i"
    else:
        im_text = _num(abs(im_p)) + "i"
    re_text = _num(re_p) if re_p != 0 else ""
    if not re_text:
        return im_text
    sign = " + " if im_p > 0 else " " + MINUS + " "
    return re_text + sign + im_text


def _num(x) -> str:
    x = sp.sympify(x)
    if isinstance(x, sp.Integer):
        return str(int(x)).replace("-", MINUS)
    if isinstance(x, sp.Rational):
        return f"{x.p}/{x.q}".replace("-", MINUS)
    return nb(x)


# ---------------------------------------------------------------- cebir
def _kisa_denklem(solution) -> list[str] | None:
    data = solution.data or {}
    eqs = data.get("equations")
    results = data.get("results")
    if not eqs or not results:
        return None
    eqs = list(eqs)
    if len(eqs) != 1:
        return _kisa_system(eqs, results)
    eq = eqs[0]
    var = next(iter(results[0].keys()), None)
    if var is None:
        return None
    expr = sp.expand(eq.lhs - eq.rhs)
    if not expr.is_polynomial(var):
        return None
    degree = sp.degree(expr, gen=var)
    if degree == 2:
        return _quadratic_lines(expr, var, results)
    if degree == 1:
        root = sp.solve(expr, var)[0]
        return [var.name + " = " + _num(root)]
    return None


def _quadratic_lines(expr, var, results) -> list[str]:
    expr = sp.expand(expr)
    a = expr.coeff(var, 2)
    b = expr.coeff(var, 1)
    c_const = expr.coeff(var, 0)
    disc = sp.simplify(b ** 2 - 4 * a * c_const)
    line_d = f"D = {_num(b ** 2)} {MINUS} {_num(4 * a * c_const)} = {_num(disc)}"
    two_a = 2 * a
    roots = [r for mapping in results for r in mapping.values()]
    if disc > 0:
        sq = sp.sqrt(disc)
        sq_text = _num(sq) if sq.is_Integer else "\u221a" + _num(sp.Integer(disc))
        line12 = ("x" + _sub("1,2") + " = (" + _num(-b) + " \u00b1 " + sq_text + ")/" + _num(two_a))
        p1 = _num(roots[0])
        p2 = _num(roots[1])
        line_roots = "x" + _sub("1") + " = " + p1 + ", " + "x" + _sub("2") + " = " + p2
        return [line_d, line12, line_roots]
    if disc == 0:
        root = sp.solve(expr, var)[0]
        return [line_d, "x = " + _num(-b) + "/" + _num(two_a) + " = " + _num(root)]
    sq = sp.sqrt(-disc)
    sq_text = _num(sq) if sq.is_Integer else "\u221a" + _num(sp.Integer(-disc))
    line12 = ("x" + _sub("1,2") + " = (" + _num(-b) + " \u00b1 " + sq_text + "i)/" + _num(two_a))
    pairs = sorted(roots, key=lambda z: complex(sp.N(z)).imag, reverse=True)
    texts = [_complex_text(r) for r in pairs]
    line_roots = ("x" + _sub("1") + " = " + texts[0] + ", " + "x" + _sub("2") + " = " + texts[1])
    return [line_d, line12, line_roots]


def _kisa_system(eqs, results) -> list[str] | None:
    if len(eqs) != 2 or len(results) != 1:
        return None
    e1, e2 = eqs
    vars_used = sorted(results[0].keys(), key=lambda s: s.name)
    if len(vars_used) != 2:
        return None
    target, other = vars_used
    o1 = sp.expand(e1.lhs).coeff(other, 1)
    o2 = sp.expand(e2.lhs).coeff(other, 1)
    if o1 + o2 == 0:
        comb = sp.expand(e1.lhs + e2.lhs)
        rhs = e1.rhs + e2.rhs
    elif o1 - o2 == 0 and o1 != 0:
        comb = sp.expand(e1.lhs - e2.lhs)
        rhs = e1.rhs - e2.rhs
    else:
        return None
    if comb.has(other):
        return None
    return [nb(comb) + " = " + nb(rhs),
            ", ".join(f"{v.name} = {_num(results[0][v])}" for v in vars_used)]


# ----------------------------------------------------------- esitsizlikler
def _kisa_inequality(solution) -> list[str] | None:
    lhs, rel, rhs = _micro_parse(solution.question)
    if lhs is None or rel == "=":
        return None
    expr = sp.expand(lhs - rhs)
    var, var_name = _single_var(expr.free_symbols)
    if var is None:
        return None
    kume = kume_yaz(sp.sympify(solution.result))
    if expr.is_polynomial(var):
        degree = sp.degree(expr, gen=var)
        if degree == 1:
            return _linear_ineq_lines(expr, var, rel)
        if degree >= 2:
            return _quadratic_ineq_lines(expr, rel, kume)
    return ["x \u2208 " + kume]


_FLIP = {"<": ">", "<=": "\u2265", ">": "<", ">=": "\u2264"}


def _linear_ineq_lines(expr, var, rel) -> list[str]:
    expr = sp.expand(expr)
    a = expr.coeff(var, 1)
    b = expr.coeff(var, 0)
    lhs_text = var.name if a == 1 else nb(a * var)
    line1 = f"{lhs_text} {rel} {_num(-b)}"
    if a < 0:
        rel = _FLIP[rel]
    root = sp.solve(expr, var)[0]
    return [line1, f"{var.name} {rel} {_num(root)}"]


def _quadratic_ineq_lines(expr, rel, kume) -> list[str]:
    factored = sp.factor(sp.expand(expr))
    coeff_bits = sp.Mul.make_args(factored)
    coeff = 1
    factors = []
    for f in coeff_bits:
        if f.is_number:
            coeff *= f
        else:
            factors.append(f)
    fv = _single_var(set().union(*[f.free_symbols for f in factors]))[0] if factors else None
    if fv is not None and len(factors) > 1:
        factors.sort(key=lambda f: (bool(f.subs(fv, 0) > 0), -f.subs(fv, 0)))
    coeff_text = ""
    if coeff != 1:
        vt = _coeff_prefix(coeff)
        coeff_text = (MINUS + vt[1]) if vt[0] else vt[1]
    parts = coeff_text + "".join(_factor_text(f) for f in factors)
    return [parts + f" {rel} 0", "x \u2208 " + kume]


# --------------------------------------------------------- mutlak deger
def _abs_data(solution):
    q = solution.question.replace("\u2212", "-").replace("\u2264", "<=").replace("\u2265", ">=")
    match = re.search(r"\|([^|]+)\|\s*(<=|>=|=|<|>)\s*(-?[\w./]+)", q)
    if not match:
        return None
    from ..utils import try_sympify as tsv
    f = tsv(match.group(1).strip())
    rel = _REL_U[match.group(2)]
    c = tsv(match.group(3))
    if f is None or c is None:
        return None
    var, _ = _single_var(f.free_symbols)
    if var is None:
        return None
    if not f.is_polynomial(var) or sp.degree(f, gen=var) != 1:
        return None
    return {"f": f, "rel": rel, "c": c, "var": var}


def _kisa_abs_eq(solution) -> list[str] | None:
    d = _abs_data(solution)
    if d is None:
        return None
    var, f, c = d["var"], d["f"], d["c"]
    roots_plus = sp.solve(sp.Eq(f, c), var)
    roots_minus = sp.solve(sp.Eq(f, -c), var)
    if len(roots_plus) != 1 or len(roots_minus) != 1:
        return None
    var_name = var.name
    return [
        f"{nb(f)} = {_num(c)} \u21d2 {var_name} = {_num(roots_plus[0])}",
        f"{nb(f)} = {_num(-c)} \u21d2 {var_name} = {_num(roots_minus[0])}",
    ]


def _kisa_abs_ineq(solution) -> list[str] | None:
    d = _abs_data(solution)
    if d is None:
        return None
    var, f, c, rel = d["var"], d["f"], d["c"], d["rel"]
    if rel in ("<", "\u2264"):
        line1 = f"{_num(-c)} {rel} {nb(f)} {rel} {_num(c)}"
        return [line1, "x \u2208 " + kume_yaz(solution.result)]
    if rel in (">", "\u2265"):
        roots_plus = sp.solve(sp.Eq(f, c), var)
        roots_minus = sp.solve(sp.Eq(f, -c), var)
        if len(roots_plus) != 1 or len(roots_minus) != 1:
            return None
        var_name = var.name
        return [
            f"{nb(f)} {rel} {_num(c)} \u21d2 {var_name} {rel} {_num(roots_plus[0])}",
            f"{nb(f)} \u2264 {_num(-c)} \u21d2 {var_name} \u2264 {_num(roots_minus[0])}",
            "x \u2208 " + kume_yaz(solution.result),
        ]
    return None


def _kisa_log_eq(solution) -> list[str] | None:
    raw = solution.question.replace("\u2212", "-")
    match = re.search(r"log_?\s*(\d*)\s*\(\s*([^()]+?)\s*\)\s*=\s*(-?[\w./]+)", raw)
    if not match:
        return None
    from ..utils import try_sympify as tsv
    base_raw, f_raw, c_raw = match.groups()
    if not base_raw:
        return None
    f = tsv(f_raw)
    c = tsv(c_raw)
    base = int(base_raw)
    if f is None or c is None:
        return None
    var, _ = _single_var(f.free_symbols)
    if var is None:
        return None
    result = solution.result
    mapping = result[0] if isinstance(result, list) else result
    root = mapping.get(var) if isinstance(mapping, dict) else None
    if root is None:
        return None
    pw = str(base) + _sup(str(int(c)))
    return [f"{nb(f)} = {pw} = {_num(base ** int(c))}", f"{var.name} = {_num(root)}"]


def _kisa_exp_eq(solution) -> list[str] | None:
    raw = solution.question.replace("\u2212", "-")
    match = re.search(r"([A-Za-z0-9./]+)\s*\^\(?\s*([^()]+?)\s*\)?\s*=\s*(-?[\w./]+)", raw)
    if not match:
        return None
    from ..utils import try_sympify as tsv
    base = tsv(match.group(1))
    f = tsv(match.group(2))
    c = tsv(match.group(3))
    if base is None or f is None or c is None or not base.is_number:
        return None
    var, _ = _single_var(f.free_symbols)
    if var is None:
        return None
    k = sp.log(c, base)
    if not k.is_number:
        return None
    k = sp.nsimplify(k)
    result = solution.result
    mapping = result[0] if isinstance(result, list) else result
    root = mapping.get(var) if isinstance(mapping, dict) else None
    if root is None:
        return None
    k_text = _num(k)
    pw = nb(base) + (_sup(k_text) if _is_plain_int(k_text) else "^(" + k_text + ")")
    f_text = nb(f)
    lhs_text = nb(base) + (_sup(f_text) if _is_plain_int(f_text) else "^(" + f_text.replace(" ", "") + ")")
    return [f"{lhs_text} = {pw}", f"{f_text} = {k_text}", f"{var.name} = {_num(root)}"]


def _is_plain_int(text: str) -> bool:
    return bool(text) and (text.isdigit() or (text.startswith(MINUS) and text[1:].isdigit()))


def _kisa_radical(solution) -> list[str] | None:
    raw = solution.question.replace("\u2212", "-")
    match = re.search(r"sqrt\(\s*([^()]+?)\s*\)\s*=\s*(.+)", raw)
    if not match:
        return None
    from ..utils import try_sympify as tsv
    f = tsv(match.group(1))
    g = tsv(match.group(2))
    if f is None or g is None:
        return None
    var, _ = _single_var(f.free_symbols | g.free_symbols)
    if var is None:
        return None
    ngh = sp.expand(g ** 2 - f)
    if not ngh.is_polynomial(var) or sp.degree(ngh, gen=var) != 2:
        return None
    candidates = list(sp.solve(ngh, var))
    if len(candidates) != 2:
        return None
    line1 = f"{nb(f)} = {nb(sp.expand(g ** 2))}"
    line2 = f"{nb(ngh)} = 0"
    cand_sorted = sorted(candidates, key=lambda v: (complex(sp.N(v)).real, complex(sp.N(v)).imag),
                          reverse=True)
    line3 = ", ".join(f"{var.name} = {_num(v)}" for v in cand_sorted)
    if g.is_polynomial(var) and sp.degree(g, gen=var) == 1:
        a = sp.expand(g).coeff(var, 1)
        b0 = sp.expand(g - a * var)
        cond = f"{var.name} \u2265 {_num(-b0 / a)}"
        valids = [v for v in cand_sorted
                  if f.subs(var, v).is_number and f.subs(var, v) >= 0
                  and g.subs(var, v).is_number and g.subs(var, v) >= 0]
        if not valids:
            return None
        line4 = cond + " \u21d2 " + ", ".join(f"{var.name} = {_num(v)}" for v in valids)
        return [line1, line2, line3, line4]
    return [line1, line2, line3]


def _kisa_basitlestir(solution) -> list[str] | None:
    q = solution.question.replace("\u2212", "-").replace("\u00b2", "^2").replace("\u00b3", "^3")
    match = re.match(r"\s*(.+?)\s+sadele", q)
    if not match:
        return None
    from ..utils import try_sympify as tsv
    orig = tsv(match.group(1))
    if orig is None or not orig.is_rational_function(_single_var(orig.free_symbols)[0]):
        return None
    num, den = sp.together(orig).as_numer_denom()
    if den == 1:
        return None
    result = solution.result
    numf = sp.factor(num)
    denf = sp.factor(den)
    den_text = "(" + nb(denf) + ")" if isinstance(denf, (sp.Add, sp.Mul)) else nb(denf)
    return [nb(numf) + "/" + den_text + " = " + nb(result)]


# --------------------------------------------------------------- analiz
def _log_unit_guard(F, var, val) -> str:
    """Sinir koyuldugunda ln(1)=0 olan terimleri 'c ln 1' olarak gosterir."""
    from ..utils import try_sympify as tsv  # noqa: F401
    total = F.subs(var, val)
    if total == 0:
        units = [L for L in F.atoms(sp.log) if L.args[0].subs(var, val) == 1]
        if units:
            tt = F
            for L in units:
                tt = tt.xreplace({L: sp.log(1, evaluate=False)})
            if not tt.free_symbols:
                return nb(tt)
    return _num(total)


def _is_plain_int(text: str) -> bool:  # noqa: F811
    text = text.strip()
    return bool(text) and (text.isdigit() or (text.startswith(MINUS) and text[1:].isdigit()))


def _nice_antiderivative(expr, var):
    """(ax+b)^n icin u-formu antiturev; digerleri icin integrate."""
    if isinstance(expr, sp.Pow) and expr.base.is_Add and expr.exp.is_Integer and expr.exp >= 1:
        a = sp.expand(expr.base).coeff(var, 1)
        b0 = sp.expand(expr.base - a * var)
        if a != 0:
            return expr.base ** (expr.exp + 1) / (a * (expr.exp + 1))
    return sp.integrate(expr, var)


def _frac_text(g) -> str:
    """'e^2 - 1'/2 gibi toplulukleri (num)/den biciminde yazar."""
    num, den = sp.together(g).as_numer_denom()
    if den == 1:
        return nb(g)
    return "(" + nb(num) + ")/" + nb(den)


def _space_before_bar(f_text: str) -> str:
    return " " if (f_text and f_text[-1].isdigit()) else ""


def _kisa_def_integral(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "integral" or data.get("bounds") in (None, "None"):
        return None
    expr = sp.sympify(data["expr"])
    var = sp.sympify(data["var"])
    lo, hi = data["bounds"]
    result = sp.sympify(data["result"])
    F = _nice_antiderivative(expr, var)
    f_text = nb(F)
    if isinstance(F, sp.Add):
        f_text = "(" + f_text + ")"
    bnds = sinirlar(lo, hi)
    head = f_text + _space_before_bar(f_text) + "|" + bnds
    has_ln = bool(F.atoms(sp.log))
    has_exp = sp.exp in {type(a) for a in sp.preorder_traversal(F)} or F.has(sp.E) and F.has(var)
    is_pure_trig = bool(F.atoms(sp.sin, sp.cos)) and not has_ln and not F.has(sp.exp)
    is_poly_number = (F.is_polynomial(var) and not has_ln and not F.has(sp.exp)
                      and lo.is_number and hi.is_number)
    if has_ln:
        fb = _log_unit_guard(F, var, hi)
        fa = _log_unit_guard(F, var, lo)
        fa_txt = "(" + fa + ")" if fa.startswith(MINUS) else fa
        return [f"{head} = {fb} {MINUS} {fa_txt} = {nb(result)}"]
    if F.has(sp.exp):
        return [f"{head} = {_frac_text(result)}"]
    if is_pure_trig:
        return [f"{head} = {nb(result)}"]
    if is_poly_number:
        fb = F.subs(var, hi)
        fa = F.subs(var, lo)
        fa_txt = "(" + _num(fa) + ")" if fa < 0 else _num(fa)
        return [f"{head} = {_num(fb)} {MINUS} {fa_txt} = {_num(result)}"]
    return [f"{head} = {nb(result)}"]


def _kisa_indef_integral(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "integral" or data.get("bounds") not in (None, "None"):
        return None
    var = sp.sympify(data["var"])
    result = sp.sympify(data["result"])
    if result == sp.log(var):
        result = sp.log(sp.Abs(var))
    return [nb(result) + " + C"]


def _kisa_area(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "area":
        return None
    var = sp.sympify(data["var"])
    lo, hi = sp.sympify(data["a"]), sp.sympify(data["b"])
    f = sp.sympify(data["f"])
    g = sp.sympify(data["g"])
    diff = sp.expand(f - g)
    F = sp.sympify(data["antiderivative"])
    result = sp.sympify(solution.result) if not isinstance(solution.result, str) else sp.sympify(solution.result)
    d_text = nb(diff)
    if diff == sp.Integer(0):
        return None
    if not isinstance(diff, sp.Add):
        sep = " " if not d_text.endswith(")") else ""
        integral_text = f"{d_text}{sep}d{var.name}"
    else:
        integral_text = f"({d_text})d{var.name}"
    f_text = _asc_text(F, var)
    if isinstance(F, sp.Add):
        f_text = "(" + f_text + ")"
    bnds = sinirlar(lo, hi)
    return [f"S = \u222b{bnds} {integral_text} = {f_text}|{bnds} = {_num(result)}"]


def _deriv_factor_text(diff, var) -> str:
    """Turev metni; gerekirse (1+x)e^x biciminde yeniden duzenler."""
    diff = sp.sympify(diff)
    diff = sp.expand(diff)
    factored = sp.factor(diff)
    if isinstance(factored, sp.Mul):
        args = sp.Mul.make_args(factored)
        if sp.exp in {type(a) for a in args}:
            adds = [a for a in args if isinstance(a, sp.Add)]
            exps = [a for a in args if isinstance(a, sp.exp)]
            others = [a for a in args if a not in adds and a not in exps]
            if len(adds) == 1 and len(exps) == 1 and not others:
                a1 = adds[0]
                t1, t2 = sp.Add.make_args(a1) if len(sp.Add.make_args(a1)) == 2 else (a1, None)
                if t2 is not None and t1.has(var) and t2.is_number:
                    t1, t2 = t2, t1
                if t1.is_number and t2 is not None:
                    return "(" + nb(t1) + " + " + nb(t2) + ")e" + _SUP_LETTER["x"]
                return "(" + nb(a1) + ")e" + _SUP_LETTER["x"]
    if _nice1_usable(diff, var):
        return _nice1(diff, var)
    return nb(diff)


def _frac_term_count(diff) -> int:
    if not isinstance(diff, sp.Add):
        return 0
    return sum(1 for t in sp.Add.make_args(diff) if sp.fraction(t)[1] != 1)


def _nice1_usable(diff, var) -> bool:
    if not isinstance(diff, sp.Add):
        return False
    return _frac_term_count(diff) >= 2


def _new_mult_text(expr):
    return nb(expr)


def _nice1(diff, var):
    """Kesir iceren turev: (num)/(payda faktor)."""
    diff = sp.sympify(diff)
    if not diff.has(var):
        return None
    if diff.is_polynomial(var):
        return None
    g = sp.cancel(sp.together(diff))
    num, den = g.as_numer_denom()
    if den == 1 or (isinstance(num, sp.Integer) and num == 0):
        return None
    denf = sp.factor(den)
    den_text = "(" + nb(denf) + ")" if isinstance(denf, (sp.Add, sp.Mul)) else nb(denf)
    num_text = nb(num)
    return "(" + num_text + ")/" + den_text if isinstance(num, sp.Add) else num_text + "/" + den_text


def _kisa_differential(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "derivative":
        return None
    expr = sp.sympify(data["expr"])
    result = solution.result
    dxd = sp.Mul(*[f for f in sp.Mul.make_args(result) if f != sp.Symbol("dx")]) if isinstance(result, sp.Basic) else None
    if dxd is None:
        return None
    order = int(data.get("order", 1))
    if order != 1:
        return None
    text = _deriv_factor_text(dxd, sp.sympify(data["var"]))
    if text.startswith("(") and not _fully_parenthesized(text):
        df_line = f"df = {text} dx"
    elif text.startswith("("):
        df_line = f"df = {text}dx"
    else:
        df_line = f"df = ({text})dx"
    return [f"f{_PRIME}({data['var']}) = {text}", df_line]


def _kisa_second_deriv(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "derivative" or str(data.get("order")) not in ("2", 2):
        return None
    var = sp.sympify(data["var"])
    expr = sp.sympify(data["expr"])
    result = sp.expand(solution.result)
    first = sp.expand(sp.diff(expr, var))
    return [f"f{_PRIME}({var.name}) = {nb(first)}",
            f"f{_DOUBLE_PRIME}({var.name}) = {nb(result)}"]


def _kisa_plain_deriv(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "derivative" or str(data.get("order")) not in ("1", 1):
        return None
    text = _deriv_factor_text(solution.result, sp.sympify(data["var"]))
    return [text]


def _kisa_limit(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "limit":
        return None
    var = sp.sympify(data["var"])
    point = sp.sympify(data["point"])
    expr = sp.sympify(data["expr"])
    result = solution.result
    result_text = result if isinstance(result, str) else nb(sp.sympify(result))
    if point == sp.oo:
        return ["lim = " + result_text]
    num, den = sp.fraction(sp.together(expr))
    if den.subs(var, point) == 0:
        fact_d = sp.factor(sp.expand(den))
        fact_n = sp.factor(sp.expand(num))
        cancelled = sp.cancel(expr)
        if var in fact_d.free_symbols and cancelled != expr:
            n_parts = "".join("(" + nb(par) + ")" if isinstance(par, (sp.Add, sp.Pow)) else nb(par)
                              for par in sp.Mul.make_args(fact_n))
            d_parts = "".join("(" + nb(par) + ")" if isinstance(par, (sp.Add, sp.Pow)) else nb(par)
                              for par in sp.Mul.make_args(fact_d))
            c_text = "(" + nb(cancelled) + ")" if isinstance(cancelled, sp.Add) else nb(cancelled)
            return [f"lim {n_parts}/{d_parts} = lim {c_text} = {result_text}"]
    if isinstance(expr, sp.Mul) and expr.has(sp.sin):
        numm, denn = sp.fraction(sp.cancel(expr))
        if numm.has(sp.sin):
            inner = numm.args[0] if isinstance(numm, sp.sin) else None
            if inner is not None and sp.simplify(inner / var).is_number:
                k = sp.simplify(inner / var)
                kx = f"{_num(k)}{var.name}" if k != 1 else var.name
                return [f"{_num(k)}\u00b7lim sin {kx}/({_num(k)}{var.name}) = {result_text}"]
    return ["lim = " + result_text]


def _kisa_ekstremum(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "ekstremum":
        return None
    var = sp.sympify(data["var"])
    expr = sp.sympify(data["expr"])
    f1 = sp.sympify(data["f1"])
    criticals = list(data["criticals"])
    classes = data["classes"]
    roots = [c for c in criticals]
    if len(roots) == 2 and {abs(r) for r in roots} == {abs(roots[0])} and roots[0] == -roots[1]:
        roots_text = "\u00b1" + _num(abs(roots[0]))
    else:
        roots_text = ", ".join(_num(r) for r in sorted(roots, key=lambda v: complex(sp.N(v))))
    lines = [f"f{_PRIME}({var.name}) = {nb(f1)} = 0 \u21d2 {var.name} = {roots_text}"]
    for sinif in ("max", "min"):
        pts = sorted([c for c, s in classes if s == sinif], key=lambda v: complex(sp.N(v)))
        if not pts:
            continue
        parcalar = [f"x_{sinif} = {_num(c)}, f({_num(c)}) = {_num(expr.subs(var, c))}" for c in pts]
        lines.append(", ".join(parcalar))
    return lines


def _kisa_closed_interval(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "closed_interval":
        return None
    var = sp.sympify(data["var"])
    expr = sp.sympify(data["expr"])
    f1 = sp.sympify(data["f1"])
    criticals = sorted(list(data["criticals"]), key=lambda v: complex(sp.N(v)))
    a, b = sp.sympify(data["a"]), sp.sympify(data["b"])
    values = {sp.sympify(k).doit() if hasattr(k, 'doit') else sp.sympify(k): sp.sympify(v)
              for k, v in dict(data["values"]).items()}
    max_c = sp.sympify(data["max_c"])
    min_c = sp.sympify(data["min_c"])
    lines = []
    if criticals:
        if len(criticals) == 2 and criticals[0] == -criticals[1]:
            roots_text = "\u00b1" + _num(abs(criticals[0]))
        else:
            roots_text = ", ".join(_num(c) for c in criticals)
        lines.append(f"f{_PRIME}({var.name}) = {nb(f1)} = 0 \u21d2 {var.name} = {roots_text}")
    noktalar = [a] + [c for c in criticals if a < c < b] + [b]
    tablo = ", ".join(f"f({_num(p)}) = {_num(values[p])}" for p in noktalar)
    lines.append(tablo)
    lines.append(f"max = {_num(expr.subs(var, max_c))}, min = {_num(expr.subs(var, min_c))}")
    return lines


def _kisa_tangent(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "tangent":
        return None
    from ..utils import try_sympify as tsv
    var = sp.sympify(data["var"])
    x0 = sp.sympify(data["x0"])
    value0 = sp.sympify(data["value0"])
    slope = sp.sympify(data["slope"])
    line = sp.sympify(data["line"])
    head = f"f({nb(x0)}) = {_num(value0)}, f{_PRIME}({nb(x0)}) = {_num(slope)}"
    mid = f"y {MINUS} {_num(value0)} = {_num(slope)}({var.name} {MINUS} {_num(x0)})" if slope != 1 else f"y {MINUS} {_num(value0)} = ({var.name} {MINUS} {_num(x0)})"
    return [head, mid, "y = " + nb(line)]


# ----------------------------------------------------------- progressiyalar
def _progressiya_data(solution):
    q = solution.question.lower()
    a1m = re.search(r"a\s*_?\s*1\s*=\s*(-?\d+)", q)
    dm = re.search(r"\bd\s*=\s*(-?\d+)", q)
    b1m = re.search(r"b\s*_?\s*1\s*=\s*(-?\d+)", q)
    qm = re.search(r"\bq\s*=\s*(-?\d+)", q)
    tarif = re.findall(r"\b([Ssab])\s*_?\s*(\d+)\b(?!\s*=)", solution.question)
    return a1m, dm, b1m, qm, tarif


def _kisa_arifmetik(solution) -> list[str] | None:
    a1m, dm, b1m, qm, tarif = _progressiya_data(solution)
    if not (a1m and dm):
        return None
    a1, d = int(a1m.group(1)), int(dm.group(1))
    result = sp.sympify(solution.result)
    lines = []
    targets = [(h.upper(), int(n)) for h, n in tarif]
    for h, n in targets:
        if h == "S":
            deger = sp.Rational((2 * a1 + (n - 1) * d) * n, 2)
            lines.append(f"S{_sub(str(n))} = (2\u00b7{a1} + {n - 1}\u00b7{d})/2 \u00b7 {n} = {_num(deger)}")
        elif h == "A":
            deger = a1 + (n - 1) * d
            lines.append(f"a{_sub(str(n))} = {a1} + {n - 1}\u00b7{d} = {_num(deger)}")
    return lines or [ _num(result)]


def _kisa_geometrik(solution) -> list[str] | None:
    a1m, dm, b1m, qm, tarif = _progressiya_data(solution)
    if not (b1m and qm):
        return None
    b1, qq = int(b1m.group(1)), int(qm.group(1))
    targets = [(h.upper(), int(n)) for h, n in tarif]
    lines = []
    for h, n in targets:
        if h == "B":
            deger = b1 * qq ** (n - 1)
            lines.append(f"b{_sub(str(n))} = {b1}\u00b7{qq}{_sup(str(n - 1))} = {_num(deger)}")
        elif h == "S":
            if qq == 1:
                continue
            deger = sp.Rational(b1 * (qq ** n - 1), qq - 1)
            lines.append(f"S{_sub(str(n))} = {b1}\u00b7({qq}{_sup(str(n))} {MINUS} 1)/({qq} {MINUS} 1) = {_num(deger)}")
    result = sp.sympify(solution.result)
    return lines or [_num(result)]


def _kisa_series(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "series":
        return None
    from ..utils import try_sympify as tsv
    body = sp.sympify(data["expr"])
    var = sp.sympify(data["var"])
    lo, hi = data["bounds"]
    result = sp.sympify(data["result"])
    if hi.is_finite and (hi - lo + 1) <= 6:
        sayilar = [tsv(sp.simplify(body.subs(var, k))) for k in range(int(lo), int(hi) + 1)]
        terimler = _signed_join([nb(v) for v in sayilar])
        return [f"S = {terimler} = {_num(result)}"]
    ilk = [nb(sp.simplify(body.subs(var, k))) for k in range(int(lo), int(lo) + 3)]
    return ["S = " + _signed_join(ilk) + " + \u2026 = " + nb(result)]


def _kisa_volume(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "integral" or solution.title != "D\u00f6nel cisim hacmi":
        return None
    var = sp.sympify(data["var"])
    square = sp.sympify(data["expr"])
    lo, hi = data["bounds"]
    result = sp.sympify(data["result"])
    F = sp.integrate(square, var)
    f_text = _asc_text(F, var)
    bnds = sinirlar(lo, hi)
    return [f"V = \u03c0\u222b{bnds} {nb(square)}d{var.name} = \u03c0({f_text})|{bnds} = {nb(result)}"]



def _kok_ozet(crits, vname: str) -> str:
    if len(crits) == 2 and sp.simplify(crits[0] + crits[1]) == 0:
        return f"{vname} = \u00b1{nb(abs(crits[0]))}"
    if not crits:
        return f"{vname} yok"
    return _koked_yaz(crits, vname)


def _kisa_inverse_trig(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "inverse_trig":
        return None
    fname = data.get("func_name") or "arcsin"
    return [f"{fname}({nb(data['arg'])}) = {nb(data['angle'])}"]


def _kisa_abs_abs(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "abs_abs":
        return None
    f, g, roots = data["f"], data["g"], data["roots"]
    vname = data["var"].name
    if not roots:
        return ["\u2205"]
    lines = [f"({nb(f)}){_sup('2')} = ({nb(g)}){_sup('2')}"]
    lines.append(_koked_yaz(roots, vname))
    return lines


def _kisa_domain(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "domain":
        return None
    vname = data["var"].name
    return [f"{vname} \u2208 {kume_yaz(data['res'])}"]


def _tek_kesir_metni(inv):
    """x/2 - 3/2 -> "(x - 3)/2" gibi tek kesir metni (mumkunse)."""
    if not inv.is_Add:
        return nb(inv)
    dens = []
    for t in inv.as_ordered_terms():
        c = t.as_coeff_Mul()[0]
        if c.is_Rational:
            dens.append(c.q)
        else:
            return nb(inv)
    if not dens:
        return nb(inv)
    d = sp.ilcm(*dens)
    num = sp.expand(d * inv)
    if not num.is_polynomial():
        return nb(inv)
    nt = nb(num)
    nt = f"({nt})" if (" " in nt or MINUS in nt) else nt
    return f"{nt}/{d}"


def _kisa_inverse_function(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "inverse_function":
        return None
    vname = data["var"].name
    return [f"f\u207b\u00b9({vname}) = {_tek_kesir_metni(data['inv'])}"]


def _kisa_compose(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "composition":
        return None
    vname = data["var"].name
    return [f"f(g({vname})) = {nb(data['comp'])}"]


def _kisa_monotonic(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "monotonicity":
        return None
    vname = data["var"].name
    lines = [f"f{_PRIME}({vname}) = {nb(data['f1'])} = 0 \u21d2 {_kok_ozet(data['crits'], vname)}"]
    res = solution.result or {}
    artan, azalan = res.get("artan"), res.get("azalan")
    if artan is not None and artan != sp.S.EmptySet:
        lines.append(f"artan {vname} \u2208 {kume_yaz(artan)}")
    if azalan is not None and azalan != sp.S.EmptySet:
        lines.append(f"azalan {vname} \u2208 {kume_yaz(azalan)}")
    return lines


def _kisa_inflection(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "inflection":
        return None
    vname = data["var"].name
    points = data["points"]
    lines = [f"f{_DOUBLE_PRIME}({vname}) = {nb(data['f2'])} = 0 \u21d2 {_kok_ozet([p for p, _ in points], vname)}"]
    if not points:
        lines.append(f"d\u00f6n\u00fcm {vname} yok")
        return lines
    if len(points) == 1:
        p, y = points[0]
        lines.append(f"d\u00f6n\u00fcm noktas\u0131 ({nb(p)}; {nb(y)})")
    else:
        text = ", ".join(f"({nb(p)}; {nb(y)})" for p, y in points)
        lines.append(f"d\u00f6n\u00fcm noktalar\u0131 {text}")
    return lines


def _kisa_division(solution) -> list[str] | None:
    data = solution.data or {}
    if data.get("kind") != "polynomial_division":
        return None
    P, D, q, r = data["P"], data["D"], data["q"], data["r"]
    return [f"{nb(P)} = ({nb(D)})({nb(q)}) + {nb(r)}"]


# ---------------------------------------------------------------- yonlendirme
def kisa_satirlar(solution):
    """Solution'dan defter-kisa zinciri; taninmayan aile icin None."""
    try:
        return _kisa_dispatch(solution)
    except Exception:
        return None


def _kisa_dispatch(solution):
    title = solution.title or ""
    solver = solution.solver or ""
    if solver == "algebra":
        if title == "Denklem \u00e7\u00f6z\u00fcm\u00fc":
            return _kisa_denklem(solution)
        if title == "Basitle\u015ftirme":
            return _kisa_basitlestir(solution)
        if title in ("\u00c7arpanlara ay\u0131rma", "\u00c7arpanlara ayirma"):
            return [nb(solution.result)]
        if title == "\u0130statistik":
            return None
    if solver == "advanced_algebra":
        if title.startswith("Binom"):
            return [nb(solution.result)]
        if title.startswith("Arifmetik"):
            return _kisa_arifmetik(solution)
        if title.startswith("Geometrik"):
            return _kisa_geometrik(solution)
        if title.startswith("Mutlak de\u011fer denklemi"):
            return _kisa_abs_eq(solution)
        if title.startswith("Mutlak de\u011fer e\u015fitsizli\u011fi"):
            return _kisa_abs_ineq(solution)
        if title.startswith("Logaritmik denklem"):
            return _kisa_log_eq(solution)
        if title.startswith("\u00dcstel denklem"):
            return _kisa_exp_eq(solution)
        if title.startswith("K\u00f6k denklemi"):
            return _kisa_radical(solution)
        if title.startswith("Logaritmik e\u015fitsizlik") or title.startswith("\u00dcstel e\u015fitsizlik"):
            return ["x \u2208 " + kume_yaz(solution.result)]
        if title.startswith("E\u015fitsizlik \u00e7\u00f6z\u00fcm\u00fc"):
            return _kisa_inequality(solution)
    if solver == "calculus":
        if title == "Belirli integral":
            return _kisa_def_integral(solution)
        if title == "Belirsiz integral":
            return _kisa_indef_integral(solution)
        if title == "Diferensiyal":
            return _kisa_differential(solution)
        if title.startswith("2. mertebeden"):
            return _kisa_second_deriv(solution)
        if title == "T\u00fcrev":
            return _kisa_plain_deriv(solution)
        if title == "Limit":
            return _kisa_limit(solution)
        if title.startswith("Sonlu toplam"):
            return _kisa_series(solution)
    if solver == "advanced_analysis":
        if title.startswith("E\u011frilerle"):
            return _kisa_area(solution)
        if title.startswith("Ekstremum"):
            return _kisa_ekstremum(solution)
        if title.startswith("Kapal\u0131 aral\u0131kta"):
            return _kisa_closed_interval(solution)
        if title.startswith("Te\u011fet"):
            return _kisa_tangent(solution)
        if title.startswith("D\u00f6nel"):
            return _kisa_volume(solution)
    if solver == "school_extra":
        if title.startswith("Ters trigonometrik"):
            return _kisa_inverse_trig(solution)
        if title.startswith("Mutlak de\u011ferli denklem |f|=|g|"):
            return _kisa_abs_abs(solution)
        if title == "Tan\u0131m k\u00fcmesi":
            return _kisa_domain(solution)
        if title == "Ters fonksiyon":
            return _kisa_inverse_function(solution)
        if title == "Fonksiyon kompozisyonu":
            return _kisa_compose(solution)
        if title == "Artan/azalan aral\u0131klar":
            return _kisa_monotonic(solution)
        if title == "D\u00f6n\u00fcm noktas\u0131":
            return _kisa_inflection(solution)
        if title == "Polinom b\u00f6lme":
            return _kisa_division(solution)
    return None
