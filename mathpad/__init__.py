"""MathPad: modüler, adım adım çözüm üreten matematik motoru."""

from .engine import MathPad, NoSolverFound, SolverError
from .notebook import Notebook
from .solvers.base import Solution, Step

__version__ = "1.0.0"

__all__ = [
    "MathPad",
    "Notebook",
    "Solution",
    "Step",
    "NoSolverFound",
    "SolverError",
    "__version__",
]
