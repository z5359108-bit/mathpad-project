"""Terminal dostu düz metin çıktısı (pretty printing)."""

from __future__ import annotations

import sympy as sp

from ..solvers.base import Step


def to_text(content) -> str:
    """İçeriği okunabilir düz metne çevir (unicode pretty print)."""
    match content:
        case sp.Basic() | sp.MatrixBase() as expr:
            return sp.pretty(expr, use_unicode=True)
        case str() as raw:
            return raw
        case None:
            return ""
        case _:
            return sp.pretty(expr_convert(content), use_unicode=True)


def expr_convert(value):
    try:
        return sp.sympify(value)
    except (sp.SympifyError, TypeError, ValueError):
        return value


def step_to_text(step: Step) -> str:
    """Bir adımı düz metne çevir."""
    if step.content is None:
        return step.latex or ""
    return to_text(step.content)
