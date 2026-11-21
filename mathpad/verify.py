"""Doğrulayıcı katman: çözücü sonucunu kullanıcıya vermeden önce bağımsız
sayısal kontrollerle yoklar.

İlke: doğrulanamayan çözüm sessizce kabul edilmez. Doğrulama kendisi
hesaplanamıyorsa (ör. tekillik, sembolik karmaşıklık) kontrol atlanır;
AMA hesaplama sonuçla çelişiyorsa hata yükseltilir ve çözüm gizlenir.
"""

from __future__ import annotations

import sympy as sp
from sympy.calculus.util import singularities
from sympy.logic.boolalg import BooleanAtom

_TABLE_TOL = 1e-6
_SAMPLES = (-2.7, -1.3, -0.4, 0.7, 1.9, 3.2, 4.6)


class VerificationError(Exception):
    """Sonuç bağımsız kontrolü geçemedi."""


def _close(a, b, tol: float = _TABLE_TOL) -> bool:
    try:
        diff = abs(a - b)
    except Exception:  # noqa: BLE001
        return False
    if diff != diff:  # NaN
        return False
    scale = max(1.0, abs(b))
    return diff <= tol * scale


def _is_number(value) -> bool:
    try:
        return bool(sp.sympify(value).is_number)
    except Exception:  # noqa: BLE001
        return False


def _finite_at(expr, var, point) -> bool:
    try:
        if point in singularities(expr, var):
            return False
        value = expr.subs(var, sp.Float(point))
        return value.is_finite is not False and value.is_real is not False
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------- denklemler
def verify_equations(data: dict) -> None:
    for solution in data.get("results", []):
        for equation in data.get("equations", []):
            diff = equation.lhs - equation.rhs
            checked = diff.subs(solution, simultaneous=True)
            if checked.free_symbols:
                continue
            value = complex(sp.N(checked))
            if abs(value) > 1e-6 and not _close(value.real, 0):
                raise VerificationError(
                    f"kök denklemini sağlamıyor: {equation} @ {solution}")
        for condition in data.get("conditions", []):
            subs = {s: v for s, v in solution.items() if s in condition.free_symbols}
            if not subs:
                continue
            evaluated = condition.subs(subs)
            if isinstance(evaluated, BooleanAtom):
                if not bool(evaluated):
                    raise VerificationError(
                        f"çözüm koşulu sağlamıyor: {condition} @ {solution}")


# ---------------------------------------------------------------- türev
def verify_derivative(data: dict) -> None:
    expr, var = data["expr"], data["var"]
    result = data["result"]
    dx = sp.Symbol("dx")
    result_core = result.subs(dx, 1) if result.has(dx) else result
    if result_core.free_symbols - {var}:
        return
    f_num = sp.lambdify(var, expr, "mpmath")
    d_num = sp.lambdify(var, result_core, "mpmath")
    checked = 0
    for sample in _SAMPLES:
        if not _finite_at(expr, var, sample):
            continue
        try:
            h = 1e-5
            approx = (f_num(sample + h) - f_num(sample - h)) / (2 * h)
            exact = d_num(sample)
        except Exception:  # noqa: BLE001
            continue
        if exact != exact:  # NaN
            continue
        checked += 1
        if not _close(float(approx), float(exact), 1e-4):
            raise VerificationError(
                f"türev sayısal kontrolü tutmadı @ x={sample}: "
                f"fark yaklaşımı {approx}, sonuç {exact}")
    if checked < 2:
        raise VerificationError("türev yeterli noktada test edilemedi")


# --------------------------------------------------------------- integral
def verify_integral(data: dict) -> None:
    expr, var = data["expr"], data["var"]
    result = data["result"]
    if _is_number(result):
        result = sp.sympify(result)
    elif not isinstance(result, sp.Basic):
        return
    bounds = data.get("bounds")
    if bounds is None:
        antiderivative = result
        f_num = sp.lambdify(var, expr, "mpmath")
        d_num = sp.lambdify(var, antiderivative, "mpmath")
        checked = 0
        for sample in _SAMPLES:
            if not _finite_at(expr, var, sample) or not _finite_at(antiderivative, var, sample):
                continue
            try:
                h = 1e-5
                approx = (d_num(sample + h) - d_num(sample - h)) / (2 * h)
            except Exception:  # noqa: BLE001
                continue
            checked += 1
            if not _close(float(approx), float(complex(f_num(sample)).real), 1e-4):
                raise VerificationError(
                    f"antitürev kontrolü tutmadı @ x={sample}: "
                    f"F'({sample}) = {approx}, f = {f_num(sample)}")
        if checked < 2:
            raise VerificationError("antitürev yeterli noktada test edilemedi")
        return
    lo, hi = bounds
    f_num = sp.lambdify(var, expr, "mpmath")
    try:
        expected = sp.N(sp.Integral(expr, (var, lo, hi)).evalf())
    except Exception:  # noqa: BLE001
        return
    if not expected.is_number or not expected.is_finite:
        return
    if not _close(float(complex(expected).real), float(complex(sp.N(result)).real), 1e-5):
        raise VerificationError(
            f"belirli integral sayısal kontrolü tutmadı: "
            f"sayısal {expected}, sonuç {result}")


# ------------------------------------------------------------------ limit
def verify_limit(data: dict) -> None:
    expr, var, point, result = data["expr"], data["var"], data["point"], data["result"]
    if _is_number(result):
        result = sp.sympify(result)
    elif not isinstance(result, sp.Basic):
        return
    if result in (sp.nan, sp.zoo) or result.has(sp.oo):
        expected_symbolic = sp.limit(expr, var, point)
        if expected_symbolic not in (sp.nan, sp.zoo) and not expected_symbolic.has(sp.oo):
            raise VerificationError(
                f"sonuç {result} ama sembolik limit {expected_symbolic}")
        return
    if not result.is_number:
        return
    try:
        expected = sp.limit(expr, var, point)
    except Exception:  # noqa: BLE001
        return
    if isinstance(expected, (sp.core.numbers.NaN,)) or expected is sp.nan:
        return
    if expected.has(sp.oo) or expected == sp.zoo:
        if not (result.has(sp.oo) or result == sp.zoo or result == sp.nan):
            raise VerificationError(
                f"limit ıraksıyor ({expected}) ama sonuç {result} verildi")
        return
    if not _close(float(complex(sp.N(expected)).real), float(complex(sp.N(result)).real)):
        raise VerificationError(
            f"limit kontrolü tutmadı: sembolik {expected}, sonuç {result}")


def verify_solution(solution) -> None:
    """Solution içindeki 'data' alanına göre bağımsız kontrol yapar."""
    data = getattr(solution, "data", None)
    if not data:
        return
    kind = data.get("kind")
    verifier = {
        "equations": verify_equations,
        "derivative": verify_derivative,
        "integral": verify_integral,
        "limit": verify_limit,
        "inverse_trig": verify_inverse_trig,
        "abs_abs": verify_abs_abs,
        "domain": verify_domain,
        "inverse_function": verify_inverse_function,
        "composition": verify_composition,
        "monotonicity": verify_monotonicity,
        "inflection": verify_inflection,
        "polynomial_division": verify_polynomial_division,
    }.get(kind)
    if verifier is None:
        return
    # Verifier asla doğrudan kullanıcı verisini bozmamalı; hesaplama
    # sırasındaki beklenmedik durumlar buradan geçmez.
    try:
        verifier(data)
    except VerificationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise VerificationError(f"doğrulayıcı hata verdi: {exc}") from None


# ------------------------------------------------------- ters trigonometrik
_PRINCIPAL_RANGES = {
    "arcsin": (-sp.pi / 2, sp.pi / 2), "asin": (-sp.pi / 2, sp.pi / 2),
    "arccos": (0, sp.pi), "acos": (0, sp.pi),
    "arctan": (-sp.pi / 2, sp.pi / 2), "atan": (-sp.pi / 2, sp.pi / 2),
    "arccot": (0, sp.pi), "acot": (0, sp.pi),
}


def verify_inverse_trig(data: dict) -> None:
    func, arg, angle = data["func"], data["arg"], data["angle"]
    expected = sp.N(func(arg))
    got = sp.N(angle)
    expected_c, got_c = complex(expected), complex(got)
    if abs(expected_c.imag) > 1e-9 or abs(got_c.imag) > 1e-9:
        raise VerificationError(
            f"ters trigonometrik deger reel cikmadi: {angle}")
    if not _close(expected_c.real, got_c.real):
        raise VerificationError(
            f"{data.get('func_name')}({arg}) kontrolu tutmadi: "
            f"beklenen {expected}, sonuc {angle}")
    aralik = _PRINCIPAL_RANGES.get(data.get("func_name"))
    if aralik is not None:
        lo, hi = complex(sp.N(aralik[0])).real, complex(sp.N(aralik[1])).real
        if not (lo - 1e-9 < got_c.real < hi + 1e-9):
            raise VerificationError(
                f"{angle}, {data.get('func_name')} asil araligi disinda ({lo}; {hi})")


# ------------------------------------------------------------------- |f|=|g|
def verify_abs_abs(data: dict) -> None:
    f, g, var, roots = data["f"], data["g"], data["var"], data["roots"]
    tru = [r for r in sp.solve(sp.expand(f ** 2 - g ** 2), var) if r.is_real is not False]
    tru = sorted((sp.N(r) for r in tru), key=lambda z: complex(z).real)
    got = sorted((sp.N(r) for r in roots), key=lambda z: complex(z).real)
    if len(tru) != len(got) or any(
            abs(complex(a).real - complex(b).real) > 1e-6 for a, b in zip(tru, got)):
        raise VerificationError(
            f"|f|=|g| kok kumesi tam degil: {got} vs {tru}")
    for r in roots:
        lr, rg = sp.N(f.subs(var, r)), sp.N(g.subs(var, r))
        absf = abs(complex(lr))
        absg = abs(complex(rg))
        if not _close(absf, absg):
            raise VerificationError(
                f"kok {r} |f|=|g| saglamyor: |{lr}| != |{rg}|")


# -------------------------------------------------------------- tanim kumesi
def _interval_ornekler_tumu(kume):
    if kume is sp.S.Reals:
        return list(_SAMPLES)
    parcalar = kume.args if isinstance(kume, sp.Union) else [kume]
    ornekler = []
    for parca in parcalar:
        if isinstance(parca, sp.Interval):
            lo, hi = parca.start, parca.end
            if lo in (-sp.oo, sp.oo) or hi in (-sp.oo, sp.oo):
                if lo == sp.oo or hi == -sp.oo:
                    continue
                if lo == -sp.oo and hi == sp.oo:
                    ornekler.append(0.0)
                elif lo == -sp.oo:
                    ornekler.append(float(sp.N(hi)) - 1.0)
                else:
                    ornekler.append(float(sp.N(lo)) + 1.0)
            else:
                lo_f, hi_f = float(sp.N(lo)), float(sp.N(hi))
                if hi_f - lo_f > 1e-12:
                    ornekler.append((lo_f + hi_f) / 2)
    return [s for s in ornekler if not (s != s)]


def verify_domain(data: dict) -> None:
    expr, var, res = data["expr"], data["var"], data["res"]
    if not isinstance(res, sp.Set):
        raise VerificationError("tanim kumesi bir kume olarak donmedi")
    if res is sp.S.EmptySet or (hasattr(res, "is_empty") and res.is_empty):
        return
    for ornek in _interval_ornekler_tumu(res):
        if not _finite_at(expr, var, ornek):
            raise VerificationError(
                f"tanim kumesi x={ornek} noktasini iceriyor ama ifade tanimsiz")


# ------------------------------------------------------------ ters fonksiyon
def verify_inverse_function(data: dict) -> None:
    expr, var, inv = data["expr"], data["var"], data["inv"]
    fark = sp.simplify(sp.expand(expr.subs(var, inv)) - var)
    fark = sp.simplify(fark)
    if fark == 0:
        return
    dx = sp.Symbol("dx")
    temiz = inv.subs(dx, 1) if inv.has(dx) else inv
    for ornek in (-1.7, 0.6, 2.3):
        try:
            f_s = sp.N(expr.subs(var, sp.N(temiz.subs(var, ornek))))
            hedef = sp.N(ornek)
        except Exception:  # noqa: BLE001
            continue
        fc, hc = complex(f_s), complex(hedef)
        if abs(fc.imag) < 1e-9 and abs(hc.imag) < 1e-9 and _close(fc.real, hc.real, 1e-6):
            return
    raise VerificationError(
        f"f(f^-1(x)) = x kontrolu tutmadi: fark {fark}")


# ------------------------------------------------------------- kompozisyon
def verify_composition(data: dict) -> None:
    f, g, comp, var = data["f"], data["g"], data["comp"], data["var"]
    beklenen = sp.expand(f.subs(var, g))
    if sp.simplify(beklenen - comp) != 0:
        raise VerificationError(
            f"f(g(x)) genislemesi tutmadi: {comp} vs {beklenen}")
    f_num = sp.lambdify(var, f, "mpmath")
    g_num = sp.lambdify(var, g, "mpmath")
    c_num = sp.lambdify(var, comp, "mpmath")
    for ornek in (-0.7, 0.9, 2.1):
        try:
            if not _close(float(g_num(ornek) * 0 + c_num(ornek)),
                          float(f_num(g_num(ornek))), 1e-6):
                raise VerificationError(
                    f"f(g({ornek})) sayisal kontrolu tutmadi")
        except VerificationError:
            raise
        except Exception:  # noqa: BLE001
            continue


# ---------------------------------------------------------- artan/azalan
def verify_monotonicity(data: dict) -> None:
    var, f1, pieces = data["var"], data["f1"], data["pieces"]
    kontrol = 0
    for a, b, yon in pieces:
        if a == -sp.oo and b == sp.oo:
            mid = sp.Integer(0)
        elif a == -sp.oo:
            mid = b - 1
        elif b == sp.oo:
            mid = a + 1
        else:
            mid = (a + b) / 2
        try:
            deger = complex(sp.N(f1.subs(var, sp.N(mid)))).real
        except Exception:  # noqa: BLE001
            continue
        if deger != deger:
            continue
        kontrol += 1
        if abs(deger) < 1e-9:
            raise VerificationError(
                f"({a}; {b}) araliginin ortasinda f' = 0 cikti")
        if (deger > 0) != (yon == "artan"):
            raise VerificationError(
                f"f'({mid}) = {deger} ama aralik {yon} denildi")
    if kontrol < 1:
        raise VerificationError("monotonluk araliklari test edilemedi")


# ------------------------------------------------------------- donum noktasi
def verify_inflection(data: dict) -> None:
    var, f2, points = data["var"], data["f2"], data["points"]
    if not points:
        return
    for r, deger in points:
        eps = sp.Rational(1, 10)
        try:
            s1 = complex(sp.N(f2.subs(var, sp.N(r) - eps))).real
            s2 = complex(sp.N(f2.subs(var, sp.N(r) + eps))).real
            f_r = complex(sp.N(deger)).real
        except Exception:  # noqa: BLE001
            continue
        if s1 * s2 >= 0:
            raise VerificationError(
                f"x={r} etrafinda f'' isaret degistirmiyor")


# ---------------------------------------------------------- polinom bolme
def verify_polynomial_division(data: dict) -> None:
    P, D, q, r, var = data["P"], data["D"], data["q"], data["r"], data["var"]
    if sp.simplify(sp.expand(P - D * q - r)) != 0:
        raise VerificationError(
            f"P = D*q + r esitligi tutmadi: {sp.expand(P - D * q - r)}")
    if sp.degree(r, var) >= sp.degree(D, var):
        raise VerificationError(
            f"kalan derecesi ({sp.degree(r, var)}) bolen derecesinden "
            f"({sp.degree(D, var)}) kucuk olmali")
