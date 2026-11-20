"""MathPad: modüler, adım adım çözüm üreten matematik motoru."""

from .engine import MathPad, NoSolverFound, SolverError
from .notebook import Notebook
from .settings import OUTPUT_MODES, Settings
from .solvers.base import Solution, Step

__version__ = "1.1.0"

__all__ = [
    "MathPad",
    "Notebook",
    "Solution",
    "Step",
    "Settings",
    "OUTPUT_MODES",
    "NoSolverFound",
    "SolverError",
    "__version__",
]
