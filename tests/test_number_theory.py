import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad
from mathpad.solvers import NumberTheorySolver


class TestNumberTheory(unittest.TestCase):
    def setUp(self):
        self.solver = NumberTheorySolver()
        self.engine = MathPad()

    def solve(self, question):
        return self.solver.solve(question)

    def test_gcd(self):
        self.assertEqual(self.solve("gcd(48, 18)").result, 6)

    def test_gcd_turkish(self):
        self.assertEqual(self.solve("48 ve 18 sayılarının ebobu").result, 6)

    def test_lcm(self):
        self.assertEqual(self.solve("ekok(4, 6)").result, 12)

    def test_prime_yes(self):
        solution = self.solve("97 asal mı?")
        self.assertIn("asaldır", solution.result_text)

    def test_prime_no(self):
        solution = self.solve("91 asal mı?")
        self.assertIn("asal değildir", solution.result_text)

    def test_factorization(self):
        solution = self.solve("360 sayısını asal çarpanlarına ayır")
        self.assertIn("2^3", solution.result_text)
        self.assertIn("3^2", solution.result_text)
        self.assertIn("5", solution.result_text)

    def test_divisors(self):
        solution = self.solve("12 sayısının bölenleri")
        self.assertEqual(list(solution.result), [1, 2, 3, 4, 6, 12])

    def test_mod_exp(self):
        self.assertEqual(self.solve("7^3 mod 100").result, 43)

    def test_mod_plain(self):
        self.assertEqual(self.solve("17 mod 5").result, 2)

    def test_combination(self):
        self.assertEqual(self.solve("C(10, 3)").result, 120)

    def test_combination_turkish(self):
        self.assertEqual(self.solve("10 elemanlı kümenin 3 elemanlı kombinasyonu").result, 120)

    def test_permutation(self):
        self.assertEqual(self.solve("P(5, 2)").result, 20)

    def test_combination_formula_steps(self):
        solution = self.solve("C(5, 2)")
        titles = [s.title for s in solution.steps]
        self.assertTrue(any("Formül" in t for t in titles))

    def test_routing_gcd(self):
        solution = self.engine.ask("48 ve 18 in ebobu")
        self.assertEqual(solution.solver, "number_theory")

    def test_routing_combination(self):
        solution = self.engine.ask("C(10, 3)")
        self.assertEqual(solution.solver, "number_theory")


if __name__ == "__main__":
    unittest.main()
