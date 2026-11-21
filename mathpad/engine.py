"""MathPad Engine: soruyu analiz edip doğru çözücüye yönlendiren katman."""

from __future__ import annotations

from .solvers import DEFAULT_SOLVERS, Solution, Solver


class NoSolverFound(Exception):
    """Hiçbir çözücü soruyu işleyemiyor."""


class SolverError(Exception):
    """Çözücü seçildi ama çözüm sırasında hata oluştu."""


class MathPad:
    """Modüler matematik motoru.

    Soruyu çözücülere dağıtır; en yüksek güven skoruna sahip çözücü çalışır.
    Yeni yetenek eklemek için register() ile bir Solver ekle - motor geri
    kalanını halleder.
    """

    def __init__(self, solvers: tuple[Solver, ...] = DEFAULT_SOLVERS, threshold: float = 0.5):
        self.solvers: list[Solver] = list(solvers)
        self.threshold = threshold
        self.history: list[Solution] = []

    def register(self, solver: Solver) -> None:
        self.solvers.append(solver)

    def route(self, question: str) -> list[tuple[float, Solver]]:
        """Çözücüleri güven skoruna göre sırala (en iyi başta)."""
        scored = [(solver.can_handle(question), solver) for solver in self.solvers]
        return sorted(scored, key=lambda pair: pair[0], reverse=True)

    def ask(self, question: str) -> Solution:
        question = question.strip()
        if not question:
            raise NoSolverFound("Soru boş olamaz.")
        ranked = self.route(question)
        best_score, best_solver = ranked[0]
        solution = None
        last_error: Exception | None = None
        attempt_threshold = min(self.threshold, 0.3)
        if best_score < attempt_threshold:
            raise NoSolverFound(
                f"Soru anlaşılamadı (en iyi aday: {best_solver.name}, skor {best_score:.2f}). "
                "Daha açık bir ifade deneyin, ör. 'x^2 - 4 = 0 denklemini çöz'."
            )
        for score, solver in ranked:
            if score < attempt_threshold:
                break
            try:
                solution = solver.solve(question)
                break
            except NoSolverFound as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = SolverError(f"{solver.name} çözücüsü hata verdi: {exc}")
                continue
        if solution is None:
            raise last_error or NoSolverFound("Hiçbir çözücü bu soruyu işleyemedi.")
        self.history.append(solution)
        return solution

    def ask_many(self, *questions: str) -> list[Solution]:
        return [self.ask(q) for q in questions]

    def defter(self, question: str) -> str:
        """Defter modu: kisa matematik zinciri (aciklama ve ondalik yok)."""
        from .rendering.defter import defter_metni

        return defter_metni(self.ask(question))
