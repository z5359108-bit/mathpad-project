"""İçerikleri LaTeX'e çeviren katman."""

from __future__ import annotations

import sympy as sp

from ..solvers.base import Step


def to_latex(content) -> str:
    """sympy nesnesi veya metni LaTeX biçimine çevir."""
    match content:
        case sp.Basic() as expr:
            return sp.latex(expr)
        case sp.MatrixBase() as mat:
            return sp.latex(mat)
        case str() as raw:
            return raw
        case None:
            return ""
        case _:
            return sp.latex(content)


def step_to_latex(step: Step) -> str:
    """Bir adımı LaTeX bloğuna çevir; açık latex varsa onu kullan."""
    if step.latex is not None:
        return step.latex
    if step.content is None:
        return ""
    return to_latex(step.content)
