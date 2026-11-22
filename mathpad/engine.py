"""MathPad Engine: soruyu analiz edip doğru çözücüye yönlendiren katman."""

from __future__ import annotations

from .solvers import DEFAULT_SOLVERS, NoSolverFound, Solution, Solver
from .verify import VerificationError, verify_solution



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
        """Çözücüleri güven skoruna göre sırala (en iyi başta).

        Bir çözücünün can_handle'ı beklemedik şekilde hiçbir sonucu bozmasın
        (ör. Boolean cinsinden istisna): hata verilmiş çözücünün skoru 0 kabul edilir.
        """
        scored: list[tuple[float, Solver]] = []
        for solver in self.solvers:
            try:
                score = float(solver.can_handle(question))
            except Exception:  # noqa: BLE001
                score = 0.0
            scored.append((score, solver))
        return sorted(scored, key=lambda pair: pair[0], reverse=True)

    def ask(self, question: str) -> Solution:
        question = question.strip()
        if not question:
            raise NoSolverFound("Soru boş olamaz.")
        ranked = self.route(question)
        best_score, best_solver = ranked[0]
        solution = None
        last_error: Exception | None = None
        first_nsf: Exception | None = None
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
                verify_solution(solution)
                break
            except NoSolverFound as exc:
                if first_nsf is None:
                    first_nsf = exc
                continue
            except VerificationError as exc:
                last_error = SolverError(
                    f"{solver.name} sonucu doğrulanamadı: {exc}")
                continue
            except Exception as exc:
                last_error = SolverError(f"{solver.name} çözücüsü hata verdi: {exc}")
                continue
        if solution is None:
            if first_nsf is not None:
                raise first_nsf
            raise last_error or NoSolverFound("Hiçbir çözücü bu soruyu işleyemedi.")
        self.history.append(solution)
        return solution

    def ask_many(self, *questions: str) -> list[Solution]:
        return [self.ask(q) for q in questions]

    def defter(self, question: str) -> str:
        """Defter modu: kisa matematik zinciri (aciklama ve ondalik yok)."""
        from .rendering.defter import defter_metni

        return defter_metni(self.ask(question))
