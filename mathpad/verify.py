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
