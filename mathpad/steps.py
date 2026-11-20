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
        return expr.as_poly(var).degree() <= 1
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
    steps = _walk_derivative(expr, var, 0, max_depth)
    if not steps:
        steps = [Step("Sonuç", content=sp.diff(expr, var))]
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
        if rest.has(var):
            _walk_integral(rest, var, depth + 1, out)
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
