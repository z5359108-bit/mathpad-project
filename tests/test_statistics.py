import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad
from mathpad.solvers import StatisticsSolver
from mathpad.solvers.statistics import _extract_list


class TestStatsUnit(unittest.TestCase):
    def setUp(self):
        self.solver = StatisticsSolver()

    def check(self, question, expected, tolerance=1e-9):
        solution = self.solver.solve(question)
        self.assertAlmostEqual(float(solution.result), expected, delta=tolerance)

    def test_extract_list_bracket(self):
        self.assertEqual(_extract_list("ortalama [3, 5, 7]"), [3.0, 5.0, 7.0])

    def test_extract_list_plain(self):
        self.assertEqual(_extract_list("3 5 7 kümenin ortalaması"), [3.0, 5.0, 7.0])

    def test_mean(self):
        self.check("ortalama [1, 2, 3, 4, 5]", 3.0)

    def test_mean_whitespace_separated(self):
        self.check("3 5 7 sayılarının ortalaması", 5.0)

    def test_english_mean(self):
        self.check("mean of [4, 8, 6]", 6.0)

    def test_median_odd(self):
        self.check("medyan [1, 2, 3, 100]", 2.5)

    def test_median_sorting(self):
        self.check("median of [10, 2, 8]", 8.0)

    def test_variance(self):
        self.check("varyans [2, 4, 4, 4, 5, 5, 7, 9]", 4.0)

    def test_std(self):
        self.check("standart sapma [2, 4, 4, 4, 5, 5, 7, 9]", 2.0)

    def test_sum(self):
        self.check("toplam [1, 2, 3]", 6.0)

    def test_max(self):
        self.check("en büyük değer [3, 9, 2]", 9.0)

    def test_min(self):
        self.check("min [3, 9, 2]", 2.0)

    def test_mode_reported_as_list(self):
        solution = self.solver.solve("modu [1, 2, 2, 3, 3, 3]")
        self.assertIn(3.0, solution.result)

    def test_routing_statistics(self):
        engine = MathPad()
        solution = engine.ask("standart sapma [2, 4, 4, 4, 5, 5, 7, 9]")
        self.assertEqual(solution.solver, "statistics")

    def test_no_numbers_raises(self):
        with self.assertRaises(ValueError):
            self.solver.solve("ortalama boş küme")


if __name__ == "__main__":
    unittest.main()
