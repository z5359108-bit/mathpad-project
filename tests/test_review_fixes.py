"""Harici incelemede bulunan hatalarin regresyon testleri.

Her test 13 maddelik hata listesinden bir maddeyi temel alir; duzeltme sonrasi
beklenen davranis sabitlenir.
"""

import unittest

import sympy as sp

from mathpad import MathPad


class TestReviewFixes(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _ask(self, question):
        return self.pad.ask(question)

    def test_directional_limit_right(self):
        sol = self._ask("limit of 1/x as x->0+")
        self.assertEqual(sol.result, sp.oo)

    def test_directional_limit_left(self):
        sol = self._ask("limit of 1/x as x->0-")
        self.assertEqual(sol.result, -sp.oo)

    def test_directional_limit_step(self):
        sol = self._ask("limit of 1/x as x->0-")
        titles = [step.title for step in sol.steps]
        self.assertTrue(any("Yönlü" in t for t in titles))

    def test_undirected_limit_still_works(self):
        sol = self._ask("limit of sin(x)/x as x->0")
        self.assertEqual(sol.result, 1)

    def test_abs_derivative_gives_sign(self):
        sol = self._ask("derivative of abs(x)")
        real_x = sp.Symbol("x", real=True)
        self.assertEqual(sol.result, sp.sign(real_x))

    def test_abs_derivative_no_complex_atoms(self):
        sol = self._ask("derivative of abs(x)")
        self.assertNotIn("re", sol.result_tex.split("(")[0])

    def test_inequality_no_solution(self):
        sol = self._ask("x^2<0")
        self.assertEqual(sol.solver, "advanced_algebra")
        self.assertEqual(sol.result, sp.EmptySet)
        self.assertTrue(any(step.title == "Çözüm yok" for step in sol.steps))

    def test_turkmen_derivative_routing(self):
        sol = self._ask("f(x)=3x^3+cos(2x)-3 differensialyny tapyn")
        self.assertEqual(sol.solver, "calculus")
        expected = 9 * sp.Symbol("x") ** 2 - 2 * sp.sin(2 * sp.Symbol("x"))
        self.assertEqual(sp.simplify(sol.result - expected), 0)

    def test_transcendental_log_equation(self):
        sol = self._ask("log_2(x)=x-3")
        values = [float(sp.N(d[sp.Symbol("x")], 10)) for d in sol.result]
        self.assertEqual(len(values), 2)
        for val in values:
            self.assertAlmostEqual(val, float(sp.log(val, 2)) + 3, places=5)

    def test_negative_integral_bounds(self):
        sol = self._ask("integral of x^2 from -2 to 2")
        self.assertEqual(sol.result, sp.Rational(16, 3))

    def test_area_constant_second_curve(self):
        sol = self._ask("y=x^2, y=4 sinirli alani hesapla")
        self.assertEqual(sol.solver, "advanced_analysis")
        self.assertEqual(sol.result, sp.Rational(32, 3))

    def test_area_vertical_bounds(self):
        sol = self._ask("y=x^4; y=1; x=-1; x=1 meydanyny tap")
        self.assertEqual(sol.solver, "advanced_analysis")
        self.assertEqual(sol.result, sp.Rational(8, 5))

    def test_closed_interval_max_min_comma(self):
        sol = self._ask("f(x)=x^2-4x+1 [0,3] max min")
        self.assertEqual(sol.solver, "advanced_analysis")
        self.assertIn("1", sol.result_tex)
        self.assertIn("-3", sol.result_tex)

    def test_abs_negative_rhs_empty(self):
        sol = self._ask("|x|=-1")
        self.assertEqual(sol.solver, "advanced_algebra")
        self.assertEqual(sol.result, sp.EmptySet)
        self.assertTrue(any("yok" in step.title for step in sol.steps))

    def test_tan_general_solution_note(self):
        sol = self._ask("tan(x)=1")
        titles = [step.title for step in sol.steps]
        self.assertTrue(any("periyodiklik" in t for t in titles))
        periodic = next(s for s in sol.steps if "periyodiklik" in s.title)
        self.assertIn("k\\pi", periodic.latex)

    def test_sin_power_notation(self):
        sol = self._ask("f(x)=sin^2(x) türevi")
        self.assertEqual(sp.simplify(sol.result - sp.sin(2 * sp.Symbol("x"))), 0)

    def test_sin_power_integral(self):
        sol = self._ask("integral of sin^2(x) from 0 to pi/2")
        self.assertEqual(sol.result, sp.pi / 4)


class TestReviewFixesUnit(unittest.TestCase):
    def test_empty_set_is_not_called(self):
        from mathpad.solvers.advanced_algebra import AdvancedAlgebraSolver

        solver = AdvancedAlgebraSolver()
        solution = solver.solve("|x|-5|=4")
        self.assertTrue(solution.result)

    def test_assemble_set_returns_emptyset_singleton(self):
        from mathpad.solvers.advanced_algebra import AdvancedAlgebraSolver

        answer = AdvancedAlgebraSolver._assemble_set([], [])
        self.assertIs(answer, sp.EmptySet)


if __name__ == "__main__":
    unittest.main()
