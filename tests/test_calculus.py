import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad
from mathpad.solvers import CalculusSolver

import sympy as sp


class TestCalculus(unittest.TestCase):
    def setUp(self):
        self.solver = CalculusSolver()
        self.engine = MathPad()
        self.x = sp.Symbol("x")

    def solve(self, question):
        return self.solver.solve(question)

    def test_derivative_polynomial(self):
        solution = self.solve("x^3 + 2*x fonksiyonunun türevi")
        self.assertEqual(sp.expand(solution.result), 3*self.x**2 + 2)

    def test_derivative_d_over_dx(self):
        solution = self.solve("d/dx sin(x)")
        self.assertEqual(solution.result, sp.cos(self.x))

    def test_second_derivative(self):
        solution = self.solve("x^4 ikinci türev")
        self.assertEqual(sp.expand(solution.result), 12*self.x**2)

    def test_derivative_english(self):
        solution = self.solve("derivative of exp(2*x)")
        self.assertEqual(solution.result, 2*sp.exp(2*self.x))

    def test_indefinite_integral(self):
        solution = self.solve("integral of x^2 dx")
        self.assertEqual(sp.expand(solution.result), self.x**3/3)

    def test_indefinite_integral_turkish(self):
        solution = self.solve("x^2 + 1'in integrali")
        self.assertEqual(sp.expand(solution.result), self.x**3/3 + self.x)

    def test_definite_integral_english(self):
        solution = self.solve("integral of x^2 from 0 to 3")
        self.assertEqual(solution.result, 9)

    def test_definite_integral_turkish(self):
        solution = self.solve("sin(x) fonksiyonunun 0 dan pi ye integrali")
        self.assertEqual(solution.result, 2)

    def test_limit(self):
        solution = self.solve("limit of sin(x)/x as x->0")
        self.assertEqual(solution.result, 1)

    def test_limit_turkish_arrow(self):
        solution = self.solve("x->2 iken (x^2-4)/(x-2) limiti")
        self.assertEqual(solution.result, 4)

    def test_limit_at_infinity(self):
        solution = self.solve("limit of (3*x + 1)/x as x->inf")
        self.assertEqual(solution.result, 3)

    def test_taylor_sin(self):
        solution = self.solve("taylor series of sin(x), 3 terms")
        expected = self.x - self.x**3/6 + self.x**5/120
        self.assertEqual(sp.expand(solution.result), expected)

    def test_taylor_exp(self):
        solution = self.solve("taylor series of exp(x), 4 terms")
        expected = 1 + self.x + self.x**2/2 + self.x**3/6
        self.assertEqual(sp.expand(solution.result), expected)

    def test_routing_derivative(self):
        solution = self.engine.ask("d/dx (x^2 + 3)")
        self.assertEqual(solution.solver, "calculus")

    def test_routing_limit(self):
        solution = self.engine.ask("limit of sin(x)/x as x->0")
        self.assertEqual(solution.solver, "calculus")

    def test_routing_integral(self):
        solution = self.engine.ask("integral of x^2 from 0 to 3")
        self.assertEqual(solution.solver, "calculus")

    def test_routing_series(self):
        solution = self.engine.ask("taylor series of cos(x)")
        self.assertEqual(solution.solver, "calculus")

    def test_finite_sum_canonical(self):
        solution = self.engine.ask("sum k=1 to 10 of k^2")
        self.assertEqual(solution.solver, "calculus")
        self.assertEqual(solution.result, 385)

    def test_finite_sum_word_no_to(self):
        solution = self.engine.ask("summation k 1 10 k^2")
        self.assertEqual(solution.solver, "calculus")
        self.assertEqual(solution.result, 385)

    def test_finite_sum_bare_keyword(self):
        solution = self.engine.ask("sum k 1 10 k^2")
        self.assertEqual(solution.solver, "calculus")
        self.assertEqual(solution.result, 385)

    def test_sum_list_still_statistics(self):
        solution = self.engine.ask("sum of [1,2,3,4]")
        self.assertEqual(solution.solver, "statistics")
        self.assertEqual(solution.result, 10.0)

    def test_extract_equations_rejects_non_basic(self):
        from mathpad.solvers.algebra import _extract_equations
        self.assertEqual(_extract_equations("sum k 1 10 k^2"), [])


if __name__ == "__main__":
    unittest.main()
