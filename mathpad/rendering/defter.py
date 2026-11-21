"""Defter modu: adim adim cozumden kisa matematik zinciri derler.

Kurallar:
- Yalnizca Step.latex satirlarindan derleme yapilir, yeni cozum uretilmez.
- Aciklama cumlesi ve ondalik yaklasik deger (\\approx) yok.
- Son cevap acilmis/sadelesmis ders kitabi biciminde: 4(3x^2-2) -> 12x^2-8,
  log(6)/5 -> (1/5)ln 6, dx'li carpanlar sonda "(...)dx".
- Diferensiyal sonuc olarak df = (...)dx bicimi kullanilir.
- \\Rightarrow, \\quad gibi ham LaTeX komutlari duz metne (⇒, bosluk) doner.
"""

from __future__ import annotations

import re

import sympy as sp

from ..solvers.base import Solution
from .latex import step_to_latex, to_latex
from .latextounicode import latex_to_unicode

_DX = sp.Symbol("dx")

_PLAIN_SUBS = (
    ("\\Rightarrow", "⇒"),
    ("\\Leftrightarrow", "⇔"),
    ("\\quad", "  "),
    ("\\qquad", "  "),
    ("\\;", " "),
    ("\\,", " "),
    ("\\ ", " "),
    ("\\cup", "∪"),
    ("\\cap", "∩"),
    ("\\subseteq", "⊆"),
    ("\\infty", "∞"),
    ("\\varnothing", "∅"),
    ("\\text{veya}", "veya"),
    ("\\text{maks}", "maks"),
    ("\\text{min}", "min"),
    ("\\max f", "maks f"),
    ("\\min f", "min f"),
    ("\\checkmark", "✓"),
    ("\\left(", "("),
    ("\\right)", ")"),
    ("\\left[", "["),
    ("\\right]", "]"),
)

_DROP_TITLE = re.compile(r"^(Verilen|E.g?riler|Fonksiyon|Tekillik|Say.sal|Kontrol|K.k kontrol|Karmasik kokler|Karmaşık kök)")

_FRAC_LN = re.compile(
    r"\\frac\{\\ln\{?\\left\(?([^(){}]*)\\right\)?\}?\}\{([^{}]+)\}")


def _plain(text: str) -> str:
    for token, replacement in _PLAIN_SUBS:
        text = text.replace(token, replacement)
    return text


def _i_fix(text: str) -> str:
    for token in ("\\mathrm{Ⅰ}", "\\mathrm{I}", "ⅈ", "𝑖"):
        text = text.replace(token, "i")
    return text


def _ln_form(text: str) -> str:
    def repl(m):
        arg = m.group(1).strip()
        if "+" in arg or "-" in arg or " " in arg:
            arg = r"\left(" + arg + r"\right)"
        return r"\frac{1}{" + m.group(2) + r"}\ln " + arg

    return _FRAC_LN.sub(repl, text)


_DOUBLE_CMD = re.compile(r"\\{2,}([A-Za-z;,.]+)")
_REL_BRACE = re.compile(r"\{\s*(<=|>=|<|>|=|\\leq|\\geq)\s*\}")


_SOFT_SUBS = (
    ("\\Rightarrow", "\u21d2"),
    ("\\Leftrightarrow", "\u21d4"),
    ("\\quad", "  "),
    ("\\qquad", "  "),
    ("\\;", " "),
)


def _soft_plain(text: str) -> str:
    for token, replacement in _SOFT_SUBS:
        text = text.replace(token, replacement)
    return text


_FRAC_LN_PREFIX = re.compile(r"(?<![\w.)])(\d+/\d+)\s*(ln\b|log\b)")


def _clean_latex(text: str) -> str:
    text = _DOUBLE_CMD.sub(r"\\\1", text)
    text = _REL_BRACE.sub(r" \1 ", text)
    text = _ln_form(_i_fix(text))
    text = _soft_plain(text)
    text = latex_to_unicode(text)
    text = _i_fix(text)
    text = _FRAC_LN_PREFIX.sub(r"(\1)\2", text)
    return text.replace("  ", " ").strip()


def _wants_factors(solution: Solution) -> bool:
    text = (solution.question + " " + " ".join(step.title for step in solution.steps)).lower()
    return bool(re.search(r"carpan|çarpan|sadele|simplify|factor", text))


def _value_latex(value) -> str:
    if isinstance(value, sp.Basic) and value.is_polynomial():
        value = sp.expand(value)
    return to_latex(value)


def _final(solution: Solution) -> str:
    result = solution.result
    if isinstance(result, str):
        return _plain(result)

    if isinstance(result, sp.Basic) and result.is_Mul and _DX in result.args:
        rest = sp.Mul(*[f for f in result.args if f != _DX])
        return _clean_latex(rf"df = \left({to_latex(rest)}\right)\,dx")

    if isinstance(result, list) and result and isinstance(result[0], dict):
        chunks = []
        for n, mapping in enumerate(result, 1):
            items = list(mapping.items())
            if len(items) == 1:
                items.sort(key=lambda kv: float(sp.re(kv[1].evalf())))
            pairs = ", ".join(
                rf"{to_latex(sym)}_{{{n}}} = {_value_latex(value)}"
                for sym, value in items
            )
            chunks.append(_clean_latex(pairs))
        return "; ".join(chunks)

    expr = result
    if isinstance(expr, sp.Basic):
        if expr == sp.nan:
            return "tanımsız"
        if expr == sp.zoo:
            return "tanımsız (∞/0 biçimi)"
        if isinstance(expr, sp.Eq):
            return _clean_latex(to_latex(expr))
        factors = expr.as_ordered_factors() if isinstance(expr, sp.Mul) else [expr]
        if _DX in factors:
            rest = sp.Mul(*[f for f in factors if f != _DX])
            return _clean_latex(rf"df = \left({to_latex(rest)}\right)\,dx")
        is_poly = bool(getattr(expr, "is_polynomial", None) and expr.is_polynomial())
        if not _wants_factors(solution) and is_poly:
            expr = sp.expand(expr)
        return _clean_latex(to_latex(expr))

    return _clean_latex(to_latex(expr))


def _same_content(step_value, result) -> bool:
    if step_value is None:
        return False
    if repr(step_value) == repr(result):
        return True
    try:
        return sp.simplify(sp.sympify(step_value) - sp.sympify(result)) == 0
    except (sp.SympifyError, TypeError, ValueError):
        return False


def _chain(solution: Solution) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for step in solution.steps:
        body = step_to_latex(step)
        if not body:
            continue
        if "\\approx" in body:
            continue
        if _same_content(step.content, solution.result):
            continue
        if step.content is None and _same_content(step_to_latex(step), _final(solution)):
            continue
        if _DROP_TITLE.search(step.title):
            continue
        if step.title.startswith("Genel çözüm") and any(
            "aralığındaki kökler" in earlier.title for earlier in solution.steps
        ):
            continue
        cleaned_probe = _clean_latex(body)
        if cleaned_probe.startswith("df = "):
            continue
        if "\\binom" in body:
            continue
        body = _clean_latex(body)
        if body in seen:
            continue
        seen.add(body)
        lines.append(body)
    return lines


def _norm(text: str) -> str:
    return text.replace("\\emptyset", "\\varnothing")


def defter_satirlar(solution: Solution) -> list[str]:
    """Kısa zincir satırları (son cevap dahil).

    Önce aile kurucu (kisa_satirlar) denenir; tanınmayan ailede genel
    zincir (adım satırlarından derleme) kullanılır.
    """
    try:
        from .kisa import kisa_satirlar
        kisa = kisa_satirlar(solution)
    except Exception:  # noqa: BLE001
        kisa = None
    if kisa:
        return kisa
    lines = _chain(solution)
    final = _final(solution)
    if not final:
        return lines
    if not lines or _norm(lines[-1]) != _norm(final):
        if _final_already_covered(final, lines):
            return lines
        lines.append(final)
    return lines


def _final_already_covered(final: str, lines: list[str]) -> bool:
    """Son cevap satırın parçaları zincirde zaten varsa tekrar ekleme."""
    parts = [p.strip(" .;") for p in final.split(";") if p.strip(" .;")]
    if not parts:
        return False
    return all(
        any(part in line for line in lines)
        for part in parts
    )


def defter_metni(solution: Solution) -> str:
    """Defter modu çıktısı: yalnızca kısa zincir; başlık/açıklama/ondalık yok."""
    return "\n".join(defter_satirlar(solution))
