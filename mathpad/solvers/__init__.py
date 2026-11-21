from .base import NoSolverFound, Solution, Step, Solver
from .arithmetic import ArithmeticSolver
from .algebra import AlgebraSolver
from .advanced_algebra import AdvancedAlgebraSolver
from .calculus import CalculusSolver
from .advanced_analysis import AdvancedAnalysisSolver
from .linear_algebra import LinearAlgebraSolver
from .number_theory import NumberTheorySolver
from .statistics import StatisticsSolver

DEFAULT_SOLVERS = (
    AdvancedAlgebraSolver(),
    AdvancedAnalysisSolver(),
    ArithmeticSolver(),
    AlgebraSolver(),
    CalculusSolver(),
    LinearAlgebraSolver(),
    NumberTheorySolver(),
    StatisticsSolver(),
)

__all__ = [
    "NoSolverFound",
    "Solver",
    "Solution",
    "Step",
    "DEFAULT_SOLVERS",
    "AdvancedAlgebraSolver",
    "AdvancedAnalysisSolver",
    "ArithmeticSolver",
    "AlgebraSolver",
    "CalculusSolver",
    "LinearAlgebraSolver",
    "NumberTheorySolver",
    "StatisticsSolver",
]
