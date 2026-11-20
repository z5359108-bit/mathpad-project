import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad
from mathpad.solvers import ArithmeticSolver
from mathpad.solvers.arithmetic import parse_percent


class TestArithmetic(unittest.TestCase):
    def setUp(self):
        self.solver = ArithmeticSolver()
        self.engine = MathPad()

    def solve(self, question):
        return self.solver.solve(question)

    def test_percent_parse_turkish(self):
        self.assertEqual(parse_percent("250'nin %15'i"), (15.0, 250.0))

    def test_percent_parse_english(self):
        self.assertEqual(parse_percent("15% of 250"), (15.0, 250.0))

    def test_percent_value(self):
        self.assertAlmostEqual(float(self.solve("250'nin %15'i").result), 37.5)

    def test_percent_yuzde_form(self):
        self.assertAlmostEqual(float(self.solve("%15'i 250").result), 37.5)

    def test_precedence(self):
        self.assertAlmostEqual(float(self.solve("(2+3)*4").result), 20.0)

    def test_powers_and_roots(self):
        self.assertAlmostEqual(float(self.solve("2^10 + sqrt(144)").result), 1036.0)

    def test_factorial(self):
        self.assertEqual(float(self.solve("5!").result), 120)

    def test_decimal_division(self):
        self.assertAlmostEqual(float(self.solve("7/2").result), 3.5)

    def test_routing_numeric_expression(self):
        solution = self.engine.ask("(2+3)*4")
        self.assertEqual(solution.solver, "arithmetic")

    def test_routing_percent(self):
        solution = self.engine.ask("250'nin %15'i")
        self.assertEqual(solution.solver, "arithmetic")

    def test_big_numbers(self):
        self.assertEqual(float(self.solve("10^6 * 2").result), 2000000)


if __name__ == "__main__":
    unittest.main()
