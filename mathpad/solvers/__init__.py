from .base import Solution, Step, Solver
from .arithmetic import ArithmeticSolver
from .algebra import AlgebraSolver
from .calculus import CalculusSolver
from .linear_algebra import LinearAlgebraSolver
from .number_theory import NumberTheorySolver
from .statistics import StatisticsSolver

DEFAULT_SOLVERS = (
    ArithmeticSolver(),
    AlgebraSolver(),
    CalculusSolver(),
    LinearAlgebraSolver(),
    NumberTheorySolver(),
    StatisticsSolver(),
)

__all__ = [
    "Solver",
    "Solution",
    "Step",
    "DEFAULT_SOLVERS",
    "ArithmeticSolver",
    "AlgebraSolver",
    "CalculusSolver",
    "LinearAlgebraSolver",
    "NumberTheorySolver",
    "StatisticsSolver",
]
