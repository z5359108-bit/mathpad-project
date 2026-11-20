import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad
from mathpad.solvers import AlgebraSolver

import sympy as sp


class TestAlgebra(unittest.TestCase):
    def setUp(self):
        self.solver = AlgebraSolver()
        self.engine = MathPad()
        self.x = sp.Symbol("x")
        self.y = sp.Symbol("y")

    def solve(self, question):
        return self.solver.solve(question)

    def test_linear_equation(self):
        results = self.solve("3*x + 4 = 10 denklemini çöz").result
        self.assertEqual(results[0][self.x], 2)

    def test_quadratic_steps(self):
        solution = self.solve("x^2 - 3x + 2 = 0")
        titles = [s.title for s in solution.steps]
        self.assertTrue(any("Diskriminant" in t for t in titles))
        values = sorted([list(row.values())[0] for row in solution.result])
        self.assertEqual(values, [1, 2])

    def test_quadratic_delta_comment(self):
        solution = self.solve("x^2 + 1 = 0")
        titles = [s.title for s in solution.steps]
        self.assertTrue(any("Diskriminant" in t for t in titles))

    def test_system_two_equations(self):
        results = self.solve("x + y = 5, x - y = 1").result
        solutions = {(row[self.x], row[self.y]) for row in results}
        self.assertIn((sp.Integer(3), sp.Integer(2)), solutions)

    def test_no_solution(self):
        solution = self.solve("x = x + 1")
        self.assertIn("yok", solution.result_text)

    def test_quadratic_title_present(self):
        solution = self.solve("x^2 - 5x + 6 = 0")
        self.assertEqual(solution.title, "Denklem çözümü")

    def test_factor(self):
        solution = self.solve("x^2 - 5x + 6 çarpanlara ayır")
        self.assertEqual(solution.result, (self.x - 2) * (self.x - 3))

    def test_expand(self):
        solution = self.solve("(x + 2)*(x + 3) expand")
        self.assertEqual(sp.expand(solution.result), self.x**2 + 5*self.x + 6)

    def test_simplify(self):
        solution = self.solve("simplify (x^2 - 1)/(x - 1)")
        self.assertEqual(sp.simplify(solution.result - (self.x + 1)), 0)

    def test_routing_equation(self):
        solution = self.engine.ask("2*x + 1 = 7")
        self.assertEqual(solution.solver, "algebra")

    def test_routing_factor(self):
        solution = self.engine.ask("x^3 - x çarpanlarına ayır")
        self.assertEqual(solution.solver, "algebra")


if __name__ == "__main__":
    unittest.main()
