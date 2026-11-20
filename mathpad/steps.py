"""Kural tabanlı, defter dilinde adım adım çözüm üreticisi.

Adımlar okul ders anlatımı gibi kurgulanır: önce kural (formül), sonra o
adımda elde edilen ifade. Yalnızca okul seviyesindeki kalıplar kurallara
bağlanır; bilinmeyen yapılar sessizce atlanır (ana sonuç her zaman sympy'den
gelir, bu katman yalnızca açıklama üretir).
"""

from __future__ import annotations

import sympy as sp

from .solvers.base import Step


def _L(expr) -> str:
    return sp.latex(expr, ln_notation=True)


_FUNC_CLASSES = (sp.sin, sp.cos, sp.tan, sp.exp, sp.log)
_FUNC_NAMES = {sp.sin: "sin", sp.cos: "cos", sp.tan: "tan", sp.exp: "e^x", sp.log: "ln"}


def _match_func(expr) -> type | None:
    for cls in _FUNC_CLASSES:
        if isinstance(expr, cls):
            return cls
    return None


def _linear_in(expr, var) -> bool:
    if not expr.has(var):
        return True
    try:
        poly = expr.as_poly(var)
        return poly is not None and poly.degree() <= 1
    except sp.PolynomialError:
        return False


# ---------------------------------------------------------------- türev

_DIFF_TABLE_RULES = {
    sp.sin: r"\frac{d}{dx}[\sin x] = \cos x",
    sp.cos: r"\frac{d}{dx}[\cos x] = -\sin x",
    sp.tan: r"\frac{d}{dx}[\tan x] = \frac{1}{\cos^{2} x}",
    sp.exp: r"\frac{d}{dx}\left[e^{x}\right] = e^{x}",
    sp.log: r"\frac{d}{dx}[\ln x] = \frac{1}{x}",
}


def derivative_steps(expr, var, max_depth: int = 3) -> list[Step]:
    steps: list[Step] = []
    quotient = _quotient_setup(expr, var)
    if quotient is not None:
        steps.extend(quotient)
    else:
        steps.extend(_walk_derivative(expr, var, 0, max_depth))
    if not steps:
        steps = [Step("Sonuç", content=sp.diff(expr, var))]
    return steps


def _quotient_setup(expr, var) -> list[Step] | None:
    """f/g biçimindeki ifadelerde bölüm kuralı adımları üretir."""
    if not expr.has(var):
        return None
    num, den = sp.fraction(sp.together(expr))
    if den == 1 or not den.has(var):
        return None
    if sp.degree(sp.expand(den), var) == 0:
        return None
    steps = [Step(
        "Bölüm (oran) kuralı",
        latex=r"\left(\frac{u}{v}\right)' = \frac{u'v - uv'}{v^{2}}",
        detail=f"u = {sp.latex(num, ln_notation=True)}, \\; v = {sp.latex(sp.expand(den), ln_notation=True)}",
    )]
    try:
        if sp.degree(sp.expand(num), var) > 0:
            steps.extend(_walk_derivative(num, var, 1, 3))
    except sp.PolynomialError:
        pass
    return steps


def _walk_derivative(expr, var, depth: int, max_depth: int) -> list[Step]:
    out: list[Step] = []
    if depth > max_depth or not expr.has(var):
        return out

    if isinstance(expr, sp.Add):
        out.append(Step(
            "Toplama-çıkarma kuralı",
            latex=r"\left(f \pm g\right)' = f' \pm g'",
            detail="her terim ayrı türetilir",
        ))
        for term in expr.as_ordered_terms():
            out.extend(_walk_derivative(term, var, depth + 1, max_depth))
        return out

    if isinstance(expr, sp.Mul):
        coeff, rest = expr.as_coeff_Mul()
        factors = [f for f in sp.Mul.make_args(rest) if f.has(var)]
        if coeff != 1:
            out.append(Step(
                "Sabit ile çarpım kuralı",
                latex=r"\left(c \cdot f\right)' = c \cdot f'",
            ))
        if len(factors) == 1:
            out.extend(_walk_derivative(factors[0], var, depth + 1, max_depth))
        elif len(factors) == 2:
            u, v = factors
            out.append(Step(
                "Çarpım kuralı",
                latex=r"\left(u \cdot v\right)' = u'v + uv'",
            ))
            out.extend(_walk_derivative(u, var, depth + 1, max_depth))
            out.extend(_walk_derivative(v, var, depth + 1, max_depth))
        return out

    if isinstance(expr, sp.Pow) and expr.exp.is_number and expr.base.has(var):
        base, n = expr.base, expr.exp
        if isinstance(base, sp.Symbol):
            out.append(Step(
                "Kuvvet (üs) kuralı",
                latex=rf"\frac{{d}}{{d{var.name}}}\left[{_L(base)}^{{{_L(n)}}}\right] = {_L(n)} \cdot {_L(base)}^{{{_L(n - 1)}}}",
            ))
        else:
            inner_slope = sp.diff(base, var)
            out.append(Step(
                "Zincir kuralı",
                latex=rf"\left(f(g)\right)' = f'(g) \cdot g', \quad g = {_L(base)}, \quad g' = {_L(inner_slope)}",
            ))
            out.extend(_walk_derivative(base, var, depth + 1, max_depth))
        return out

    cls = _match_func(expr)
    if cls is not None:
        arg = expr.args[0]
        out.append(Step(f"Türev tablosu ({_FUNC_NAMES[cls]})", latex=_DIFF_TABLE_RULES[cls]))
        if not arg.has(var):
            return out
        slope = sp.diff(arg, var)
        if slope != 1:
            out.append(Step(
                "Zincir kuralı (iç fonksiyon lineer)",
                latex=rf"u = {_L(arg)} \Rightarrow u' = {_L(slope)}, \quad \left(f(u)\right)' = f'(u) \cdot u'",
            ))
        else:
            out.extend(_walk_derivative(arg, var, depth + 1, max_depth))
        return out

    return out


# ---------------------------------------------------------------- integral

_INT_TABLE_RULES = [
    (
        lambda e, v: e == v,
        r"\int x \, dx = \frac{x^{2}}{2} + C",
    ),
    (
        lambda e, v: isinstance(e, sp.exp),
        r"\int e^{ax} \, dx = \frac{e^{ax}}{a} + C",
    ),
    (
        lambda e, v: isinstance(e, sp.Pow) and e.base == v and e.exp.is_number and e.exp == -1,
        r"\int \frac{1}{x} \, dx = \ln|x| + C",
    ),
    (
        lambda e, v: isinstance(e, sp.Pow) and e.base == v and e.exp.is_number,
        r"\int x^{n} \, dx = \frac{x^{n+1}}{n+1} + C \quad (n \neq -1)",
    ),
    (
        lambda e, v: isinstance(e, sp.sin) and _linear_in(e.args[0], v),
        r"\int \sin(ax+b) \, dx = -\frac{\cos(ax+b)}{a} + C",
    ),
    (
        lambda e, v: isinstance(e, sp.cos) and _linear_in(e.args[0], v),
        r"\int \cos(ax+b) \, dx = \frac{\sin(ax+b)}{a} + C",
    ),
]


def integral_steps(expr, var) -> list[Step]:
    out: list[Step] = []
    _walk_integral(expr, var, 0, out)
    if not out:
        out = [Step("Integral kuralı", detail="standart olmayan yapı; sonuç doğrudan hesaplandı")]
    return out


def _walk_integral(expr, var, depth: int, out: list[Step]) -> None:
    if depth > 3:
        return

    if isinstance(expr, sp.Add):
        out.append(Step(
            "Toplama-çıkarma kuralı",
            latex=r"\int \left(f \pm g\right) dx = \int f \, dx \pm \int g \, dx",
            detail="her terim ayrı integre edilir",
        ))
        for term in expr.as_ordered_terms():
            if not term.has(var):
                continue
            out.append(Step("Terim", content=term))
            _walk_integral(term, var, depth + 1, out)
        return

    if isinstance(expr, sp.Mul):
        coeff, rest = expr.as_coeff_Mul()
        if coeff != 1:
            out.append(Step(
                "Sabit ile çarpım kuralı",
                latex=r"\int c \cdot f \, dx = c \int f \, dx",
            ))
        u_sub = _exp_u_sub(rest, var)
        if u_sub is not None:
            inner, inner_slope = u_sub
            out.append(Step(
                "Değişken değiştirme",
                latex=rf"u = {_L(inner)}, \quad du = {_L(inner_slope)} \, d{var.name}",
            ))
            out.append(Step("Bu terimin integrali", content=sp.integrate(expr, var)))
            return
        if _by_parts(out, rest, var):
            return
        if rest.has(var):
            _walk_integral(rest, var, depth + 1, out)
        return

    if isinstance(expr, sp.Pow) and isinstance(expr.base, (sp.sin, sp.cos)) and expr.exp == 2:
        out.append(Step(
            "Yarı açı özdeşliği",
            latex=rf"{_L(expr)} = \frac{{1 - {_L(sp.cos(2 * var))}}}{{2}}",
            detail=r"sin^2 ve cos^2 kalıpları yarı açı formülüyle açılır",
        ))
        out.append(Step("Bu terimin integrali", content=sp.integrate(expr, var)))
        return

    for check, rule in _INT_TABLE_RULES:
        if check(expr, var):
            out.append(Step("Integral kuralı", latex=rule))
            out.append(Step("Bu terimin integrali", content=sp.integrate(expr, var)))
            return

    if isinstance(expr, sp.Pow) and expr.exp.is_number and expr.base.has(var) and _linear_in(expr.base, var):
        if isinstance(expr.base, sp.Symbol):
            out.append(Step(
                "Kuvvet kuralı",
                latex=r"\int x^{n} \, dx = \frac{x^{n+1}}{n+1} + C \quad (n \neq -1)",
            ))
        else:
            slope = sp.diff(expr.base, var)
            out.append(Step(
                "Değişken değiştirme (u = ax + b)",
                latex=rf"u = {_L(expr.base)}, \quad du = {_L(slope)} \, d{var.name}",
            ))
        out.append(Step("Bu terimin integrali", content=sp.integrate(expr, var)))
        return

    cls = _match_func(expr)
    if cls is not None and expr.args[0].has(var) and _linear_in(expr.args[0], var):
        slope = sp.diff(expr.args[0], var)
        out.append(Step(
            "Değişken değiştirme (u = ax + b)",
            latex=rf"u = {_L(expr.args[0])}, \quad du = {_L(slope)} \, d{var.name}",
        ))
        out.append(Step("Bu terimin integrali", content=sp.integrate(expr, var)))
        return

    out.append(Step("Genel integral", content=sp.integrate(expr, var)))


# ------------------------------------------------------------ kısmi integrasyon

def _classify_integral_factor(factor, var):
    """Faktörü (poly, transandant, other) sınıfına ayırır."""
    if _linear_in(factor, var):
        return "poly"
    if isinstance(factor, (sp.log, sp.exp, sp.sin, sp.cos)):
        return "trans"
    return "other"


def _by_parts(out: list[Step], expr, var) -> bool:
    """x·lnx, x·cosx, x·e^x, ln x kalıpları için kısmi integrasyon adımları."""
    if isinstance(expr, sp.log) and expr.args[0] == var:
        u, dv_expr = expr, sp.Integer(1)
        v = var
        du = 1 / var
        remaining = sp.integrate(v * du, var)
        out.append(Step(
            "Kısmi integrasyon",
            latex=r"\int u \, dv = uv - \int v \, du",
            detail="u = ln x, dv = dx",
        ))
        out.append(Step("v ve du", latex=r"v = x, \quad du = \frac{1}{x} \, dx"))
        out.append(Step("v·du'nun integrali",
                        latex=rf"\int x \cdot \frac{{1}}{{x}} \, dx = \int dx = {var}"))
        out.append(Step("Birleştir", content=sp.integrate(expr, var)))
        return True
    if not isinstance(expr, sp.Mul):
        return False
    factors = [f for f in sp.Mul.make_args(expr) if f.has(var)]
    if len(factors) != 2:
        return False
    classes = [_classify_integral_factor(f, var) for f in factors]
    if sorted(classes) != ["poly", "trans"]:
        return False
    poly_f = factors[classes.index("poly")]
    trans_f = factors[classes.index("trans")]
    if isinstance(trans_f, (sp.sin, sp.cos, sp.exp)) and not _linear_in(trans_f.args[0], var):
        return False
    if poly_f.is_number or (isinstance(poly_f, sp.Pow) and poly_f.exp < 0):
        return False
    if isinstance(trans_f, sp.log):
        u, dv_expr = trans_f, poly_f
    else:
        u, dv_expr = poly_f, trans_f
    du = sp.diff(u, var)
    v = sp.integrate(dv_expr, var)
    remaining_integrand = sp.simplify(v * du)
    v_head = sp.latex(v, ln_notation=True)
    u_head = sp.latex(u, ln_notation=True)
    dv_head = sp.latex(dv_expr, ln_notation=True)
    du_head = sp.latex(du, ln_notation=True)
    out.append(Step(
        "Kısmi integrasyon",
        latex=r"\int u \, dv = uv - \int v \, du",
        detail=f"u = {_L(u)}, dv = {_L(dv_expr)} dx seçildi",
    ))
    out.append(Step("u, dv seçimi ve v, du",
                    latex=rf"u = {u_head}, \quad dv = {dv_head} \, d{var.name} \Rightarrow v = {v_head}, \quad du = {du_head} \, d{var.name}"))
    result = sp.integrate(expr, var)
    out.append(Step("v·du'nun integrali",
                    latex=rf"\int {sp.latex(remaining_integrand, ln_notation=True)} \, d{var.name} = {sp.latex(sp.integrate(remaining_integrand, var), ln_notation=True)}"))
    out.append(Step("Birleştir", content=result))
    return True


def _exp_u_sub(expr, var):
    """x·e^(a·x² + ...) kalıbı için (inner, slope) döndürür."""
    if not isinstance(expr, sp.Mul):
        return None
    factors = [f for f in sp.Mul.make_args(expr) if f.has(var)]
    if len(factors) != 2:
        return None
    exps = [f for f in factors if isinstance(f, sp.exp) and not _linear_in(f.args[0], var)]
    polys = [f for f in factors if _linear_in(f, var) and not f.is_number]
    if len(exps) != 1 or len(polys) != 1:
        return None
    inner = exps[0].args[0]
    outer = polys[0]
    slope = sp.diff(inner, var)
    if sp.simplify(outer / slope) != 1 and sp.degree(sp.Poly(outer, var) if outer.is_polynomial(var) else outer, var) not in (0, 1):
        return None
    return inner, slope


# ---------------------------------------------------------------- limit

def limit_steps(expr, var, value) -> list[Step]:
    steps: list[Step] = []
    num, den = expr.as_numer_denom()

    zero_over_zero = False
    try:
        zero_over_zero = bool(value.is_finite) and num.subs(var, value) == 0 and den.subs(var, value) == 0
    except Exception:  # noqa: BLE001
        zero_over_zero = False

    if zero_over_zero:
        steps.append(Step(
            "0/0 belirsizliği",
            latex=rf"x \to {_L(value)} \Rightarrow \frac{{{_L(num)}}}{{{_L(den)}}} = \frac{{0}}{{0}}",
            detail="doğrudan yerine koyma yetmez",
        ))
        standard = _standard_exp_limit(num, den, var, value)
        if standard:
            return steps + standard
        simplified = _cancel_common_factor(expr, var)
        if simplified is not None:
            steps.append(Step(
                "Ortak çarpanı sadeleştir",
                latex=rf"\frac{{{_L(num)}}}{{{_L(den)}}} = {_L(simplified)}",
            ))
            result = sp.limit(simplified, var, value, "+-")
            steps.append(Step(
                "Sadeleştirilmiş biçimde hesapla",
                latex=rf"x \to {_L(value)} \Rightarrow {_L(simplified)} = {_L(result)}",
            ))
            return steps
        steps.append(Step(
            "L'Hôpital kuralı",
            latex=r"\lim \frac{f(x)}{g(x)} = \lim \frac{f'(x)}{g'(x)} \quad \left(\frac{0}{0}\right)",
        ))
        f1, g1 = sp.diff(num, var), sp.diff(den, var)
        steps.append(Step("Türetilmiş kesir", latex=rf"\frac{{ {_L(f1)} }}{{ {_L(g1)} }}"))
        special = _special_trig_limit(f1 / g1, var, value)
        if special:
            return steps + special
        try:
            num_at, den_at = f1.subs(var, value), g1.subs(var, value)
            if den_at != 0:
                steps.append(Step(
                    "L'Hôpital sonrası yerine koyma",
                    latex=rf"x = {_L(value)} \Rightarrow \frac{{ {_L(num_at)} }}{{ {_L(den_at)} }} = {_L(sp.simplify(num_at / den_at))}",
                ))
        except (TypeError, ValueError, ZeroDivisionError):
            pass
        return steps

    if value.is_infinite:
        comparison = _degree_comparison(num, den, var)
        if comparison is not None:
            n_num, n_den, lead = comparison
            steps.append(Step(
                "Sonsuzda derece kuralı",
                latex=rf"\deg(\text{{pay}}) = {n_num}, \quad \deg(\text{{payda}}) = {n_den}",
                detail="rasyonel ifadelerde sonsuzdaki limit baş katsayılardan bulunur",
            ))
            if n_num < n_den:
                verdict =rf"\lim = 0 \quad (n < m)"
            elif n_num == n_den:
                verdict = rf"\lim = {_L(lead)} \quad (n = m, \text{{baş katsayı oranı}})"
            else:
                verdict = r"\lim = \pm\infty \quad (n > m)"
            steps.append(Step("Kuralın sonucu", latex=verdict))
            return steps

    special = _special_trig_limit(expr, var, value)
    if special:
        return special

    try:
        direct = expr.subs(var, value)
    except Exception:  # noqa: BLE001
        direct = None
    if direct is not None and direct.is_finite is not False:
        steps.append(Step(
            "Doğrudan yerine koyma",
            latex=rf"{var.name} = {_L(value)} \Rightarrow {_L(direct)}",
            detail="fonksiyon noktada tanımlı ve süreklidir",
        ))
    return steps


def _cancel_common_factor(expr, var):
    try:
        simplified = sp.cancel(sp.together(expr))
        if simplified == expr:
            return None
        if sp.simplify(sp.expand(simplified - expr)) != 0:
            return None
        return simplified
    except Exception:  # noqa: BLE001
        return None


def _degree_comparison(num, den, var):
    try:
        n_num = sp.degree(num, var)
        n_den = sp.degree(den, var)
        if n_num is None or n_den is None:
            return None
        lead = sp.simplify(sp.LC(num, var) / sp.LC(den, var)) if n_num == n_den else None
        return (int(n_num), int(n_den), lead)
    except (sp.PolynomialError, AttributeError, TypeError):
        return None


def _standard_exp_limit(num, den, var, value) -> list[Step] | None:
    """(e^{a·t} - 1)/(m·t) → a/m kalıbı için standart limit adımı."""
    if value != 0 or not isinstance(num, sp.Add):
        return None
    iexps = [t for t in num.free_symbols]  # noqa: F841 - yer tutucu
    exp_terms = [t for t in num.as_ordered_terms() if isinstance(t, sp.exp) and _linear_in(t.args[0], var)]
    if len(exp_terms) != 1:
        return None
    exp_term = exp_terms[0]
    others = [t for t in num.as_ordered_terms() if t != exp_term]
    if len(others) != 1 or not others[0].is_number:
        return None
    try:
        if sp.simplify(exp_term + others[0]) != num:
            return None
        if exp_term.subs(var, value) + others[0].subs(var, value) != 0:
            return None
        result = sp.limit(num / den, var, value, "+-")
    except Exception:  # noqa: BLE001
        return None
    inner = exp_term.args[0]
    k = sp.diff(inner, var)
    den_coeff = sp.diff(den, var) if den.is_polynomial(var) and sp.degree(den, var) == 1 else None
    if den_coeff is None:
        return None
    return [
        Step(
            "Önemli standart limit",
            latex=r"\lim_{t \to 0} \frac{e^{t} - 1}{t} = 1",
            detail=f"t = {_L(inner)}",
        ),
        Step(
            "Katsayıları düzenle",
            latex=rf"\lim_{{ {var.name} \to 0 }} \frac{{ e^{{ {_L(inner)} }} - 1 }}{{ {_L(den)} }} = {_L(result)}",
        ),
    ]


def _special_trig_limit(expr, var, value):
    if value != 0:
        return None
    num, den = expr.as_numer_denom()
    for atom in num.atoms(sp.sin):
        inner = atom.args[0]
        if den == var and _linear_in(inner, var):
            k = sp.diff(inner, var)
            return [
                Step(
                    "Önemli trigonometrik limit",
                    latex=r"\lim_{t \to 0} \frac{\sin t}{t} = 1",
                    detail=f"t = {_L(inner)}",
                ),
                Step(
                    "Katsayıyı dışarı çıkar",
                    latex=rf"\lim_{{x \to 0}} \frac{{\sin({_L(inner)})}}{{{_L(var)}}} = {_L(k)}",
                ),
            ]
    for atom in num.atoms(sp.cos):
        if atom.args[0] == var:
            return [
                Step(
                    "Önemli trigonometrik limit",
                    latex=r"\lim_{t \to 0} \frac{1 - \cos t}{t^{2}} = \frac{1}{2}",
                )
            ]
    return None


# ---------------------------------------------------------------- lineer denklem

def linear_eq_steps(eq: sp.Eq, var) -> list[Step]:
    """a·x + b = c kalıbını okul yöntemiyle çözen adımlar."""
    steps: list[Step] = []
    lhs, rhs = sp.expand(eq.lhs), sp.expand(eq.rhs)
    if (lhs, rhs) != (eq.lhs, eq.rhs):
        steps.append(Step(
            "Parantezleri aç ve iki tarafı düzenle",
            latex=rf"{_L(lhs)} = {_L(rhs)}",
        ))
    poly = sp.Poly(lhs - rhs, var)
    a, b = sp.Rational(poly.all_coeffs()[0]), sp.Rational(poly.all_coeffs()[1])
    steps.append(Step(
        "Bilinmeyenli terimler bir tarafta, sabitler diğer tarafta",
        latex=rf"{_L(sp.expand(a * var))} = {_L(sp.expand(-b))}",
    ))
    if a != 1:
        steps.append(Step(
            f"Her iki tarafı {_L(a)}'ye böl",
            latex=rf"\frac{{ {_L(sp.expand(a * var))} }}{{ {_L(a)} }} = \frac{{ {_L(sp.expand(-b))} }}{{ {_L(a)} }}",
        ))
    root = sp.solve(eq, var)[0]
    steps.append(Step("Kök", latex=rf"{_L(var)} = {_L(root)}"))
    try:
        left_at, right_at = lhs.subs(var, root), rhs.subs(var, root)
        ok = sp.simplify(left_at - right_at) == 0
        steps.append(Step(
            "Kontrol",
            latex=(rf"{_L(var)} = {_L(root)} \Rightarrow {_L(left_at)} = {_L(right_at)} \;\checkmark"
                   if ok else
                   rf"{_L(var)} = {_L(root)} \Rightarrow {_L(left_at)} \approx {_L(right_at)}"),
        ))
    except Exception:  # noqa: BLE001
        pass
    return steps
