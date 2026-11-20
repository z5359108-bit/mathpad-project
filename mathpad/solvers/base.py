"""Çözücü arayüzü ve çözüm veri yapıları."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..utils import fold_turkmen


@dataclass
class Step:
    """Çözüm adımı: başlık + içerik (sympy ifadesi, metin veya hazır LaTeX)."""

    title: str
    content: Any = None
    latex: str | None = None
    detail: str | None = None


@dataclass
class Solution:
    """Tek bir sorunun tam çözümü."""

    question: str
    solver: str
    title: str
    result: Any
    result_tex: str
    result_text: str
    steps: list[Step] = field(default_factory=list)


class Solver(ABC):
    """Tüm çözücülerin temel sınıfı.

    Her çözücü iki şey yapar: soruyu kendisi için ne kadar uygun olduğunu
    söylemek (can_handle) ve çözümü adım adım üretmek (solve).
    """

    name: str = "solver"
    title: str = "Çözücü"

    @abstractmethod
    def can_handle(self, question: str) -> float:
        """0.0-1.0 arası güven skoru döndür."""

    @abstractmethod
    def solve(self, question: str) -> Solution:
        """Soruyu çözüp Solution döndür."""

    @staticmethod
    def _score(question: str, strong: tuple[str, ...], weak: tuple[str, ...] = ()) -> float:
        """Anahtar kelime puanlaması: güçlü kelime 0.45, zayıf 0.15."""
        q = fold_turkmen(question).lower()
        score = 0.0
        strong_hits = sum(1 for w in strong if w in q)
        score += min(strong_hits, 2) * 0.45
        weak_hits = sum(1 for w in weak if w in q)
        score += min(weak_hits, 3) * 0.15
        return min(score, 1.0)
