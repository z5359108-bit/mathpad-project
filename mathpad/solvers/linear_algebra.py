"""Lineer cebir çözücü: determinant, ters, özdeğer/özvektör, rank, iz, matris çarpımı."""

from __future__ import annotations

import ast
import re

import sympy as sp

from ..rendering.latex import to_latex
from ..rendering.text import to_text
from ..utils import fold_turkmen, normalize, parse_matrix
from .base import Solution, Solver, Step

_KW_STRONG = ("matris", "matrix", "determinant", "det", "özdeğer", "ozdeger", "eigen",
              "özvektör", "eigenvector", "ters", "inverse", "rank", "iz", "trace",
              "transpoze", "transpose", "devrik")
_KW_WEAK = ("lineer", "linear", "vektor", "vektör", "vector", "kare", "carp", "carpim", "system")
_OP_PATTERNS = {
    "determinant": re.compile(r"determinant|det\b|sarrus", re.IGNORECASE),
    "inverse": re.compile(r"inverse|tersini|ters matris|tersini al", re.IGNORECASE),
    "eigen": re.compile(r"ozdeger|ozvektor|eigen|karakteristik", re.IGNORECASE),
    "rank": re.compile(r"\brank\b|kerte", re.IGNORECASE),
    "trace": re.compile(r"\btrace\b|\biz\b", re.IGNORECASE),
    "transpose": re.compile(r"transpoze|transpose|devrik", re.IGNORECASE),
    "multiply": re.compile(r"carp|multiply|times|\btimes\b", re.IGNORECASE),
}
_MATRICES = re.compile(
    r"\[\s*\[[^\[\]]*\](?:(?:\s*,\s*|\s*;\s*)\[[^\[\]]*\])*\s*\]"
)


def _parse_matrices(text: str) -> list[sp.Matrix]:
    return [
        sp.Matrix(ast.literal_eval(raw.replace(";", ",")))
        for raw in _MATRICES.findall(text)
    ]


class LinearAlgebraSolver(Solver):
    name = "linear_algebra"
    title = "Lineer Cebir"

    def can_handle(self, question: str) -> float:
        q = question.lower()
        matrix_score = 0.7 if _MATRICES.search(q) else 0.0
        keyword_score = self._score(q, strong=_KW_STRONG, weak=_KW_WEAK)
        return min(max(matrix_score, keyword_score), 1.0)

    def solve(self, question: str) -> Solution:
        matrices = _parse_matrices(normalize(question.replace("×", "*")))
        if not matrices:
            raise ValueError("Soruda [[a,b],[c,d]] biçiminde bir matris bulunamadı.")
        operation = self._operation(question)
        steps = [Step("Verilen matris" + ("ler" if len(matrices) > 1 else ""),
                      content=matrices[0] if len(matrices) == 1 else " \\quad ".join(to_latex(m) for m in matrices))]
        result, label = self._apply(operation, matrices, question, steps)
        steps.append(Step("Sonuç", content=result))
        return self._solution(question, result, steps, label)

    def _operation(self, question: str) -> str:
        q = fold_turkmen(question).lower()
        for op_name, pattern in _OP_PATTERNS.items():
            if pattern.search(q):
                return op_name
        return "determinant"

    def _apply(self, operation: str, matrices: list[sp.Matrix], question: str, steps: list[Step]):
        matrix1, matrix2 = matrices[0], matrices[-1]
        match operation:
            case "determinant":
                det = matrix1.det()
                if matrix1.rows == 2 and matrix1.cols == 2:
                    a, b = matrix1.row(0)
                    c, d = matrix1.row(1)
                    steps.append(Step(
                        "Sarrus (2x2) formülü",
                        latex=f"ad - bc = ({to_latex(a)})({to_latex(d)}) - ({to_latex(b)})({to_latex(c)})",
                    ))
                return sp.simplify(det), "Determinant"
            case "inverse":
                if matrix1.det() == 0:
                    raise ValueError("Matris tekil (determinant 0); tersi yok.")
                steps.append(Step("Determinant kontrolü", content=matrix1.det()))
                return matrix1.inv(), "Matris tersi"
            case "eigen":
                eigenvals = matrix1.eigenvals()
                steps.append(Step("Karakteristik denklem kökleri (özdeğerler, katlarıyla)",
                                  content=[(val, mult) for val, mult in eigenvals.items()]))
                eigenvects = matrix1.eigenvects()
                vectors = [vec for _, _, vecs in eigenvects for vec in vecs]
                steps.append(Step("Özvektörler", content=vectors))
                return {"özdeğerler": list(eigenvals.keys()), "özvektörler": vectors}, "Özdeğer ve özvektörler"
            case "rank":
                return matrix1.rank(), "Rank (kerte)"
            case "trace":
                return matrix1.trace(), "İz (trace)"
            case "transpose":
                return matrix1.T, "Transpoze"
            case "multiply":
                if len(matrices) < 2:
                    raise ValueError("Matris çarpımı için [[..]] [[..]] biçiminde iki matris gerekli.")
                if matrix1.cols != matrix2.rows:
                    raise ValueError(
                        f"Boyut uyumsuz: ({matrix1.rows}x{matrix1.cols}) · ({matrix2.rows}x{matrix2.cols})"
                    )
                return matrix1 * matrix2, "Matris çarpımı"
            case _:
                return matrix1.det(), "Determinant"

    def _solution(self, question: str, result, steps: list[Step], title: str) -> Solution:
        if isinstance(result, dict):
            parts = []
            for key, value in result.items():
                items = value if isinstance(value, list) else [value]
                rendered = ",\\; ".join(to_latex(item) for item in items)
                parts.append(f"\\text{{{key}}}: \\left\\{{ {rendered} \\right\\}}")
            tex = "\\quad ".join(parts)
            return Solution(
                question=question, solver=self.name, title=title, result=result,
                result_tex=tex, result_text=to_text(result), steps=steps,
            )
        return Solution(
            question=question, solver=self.name, title=title, result=result,
            result_tex=to_latex(result), result_text=to_text(result), steps=steps,
        )
