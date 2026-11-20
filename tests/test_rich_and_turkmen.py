import unittest

import sympy as sp

from mathpad import MathPad
from mathpad.steps import linear_eq_steps


class TestRichSteps(unittest.TestCase):
    def setUp(self):
        self.engine = MathPad()

    def _ask(self, question):
        return self.engine.ask(question)

    def test_linear_equation_has_school_steps(self):
        sol = self._ask("3x + 4 = 10 denklemini çöz")
        titles = [s.title for s in sol.steps]
        self.assertIn("Kök", titles)
        self.assertIn("Kontrol", titles)
        self.assertTrue(any("tarafa" in t or "böl" in t for t in titles))
        self.assertGreaterEqual(len(sol.steps), 5)
        self.assertEqual(sol.result, [{sp.Symbol("x"): 2}])

    def test_linear_eq_steps_direct(self):
        x = sp.Symbol("x")
        steps = linear_eq_steps(sp.Eq(2 * x - 7, 3), x)
        self.assertTrue(any("böl" in s.title for s in steps))
        self.assertEqual(steps[-2].title, "Kök")

    def test_quadratic_has_formula_step(self):
        sol = self._ask("x^2 - 4x + 1 = 0")
        titles = [s.title for s in sol.steps]
        self.assertIn("Kök formülü", titles)
        self.assertIn("Diskriminant formülü", titles)
        self.assertIn("Katsayılar", titles)

    def test_derivative_product_rule_steps(self):
        sol = self._ask("d/dx x^2*sin(x)")
        titles = [s.title for s in sol.steps]
        self.assertIn("Çarpım kuralı", titles)
        self.assertTrue(any("üs" in t for t in titles))
        self.assertTrue(any("tablosu" in t for t in titles))

    def test_derivative_chain_rule_steps(self):
        sol = self._ask("derivative of exp(2*x)")
        titles = [s.title for s in sol.steps]
        self.assertTrue(any("Zincir kuralı" in t for t in titles))
        self.assertEqual(sp.simplify(sol.result - 2 * sp.exp(2 * sp.Symbol("x"))), 0)

    def test_integral_sum_rule_steps(self):
        sol = self._ask("integral of (3*x^2 + 2*x) dx")
        titles = [s.title for s in sol.steps]
        self.assertIn("Toplama-çıkarma kuralı", titles)
        self.assertIn("Integral kuralı", titles)

    def test_integral_substitution_steps(self):
        sol = self._ask("integral of (2*x + 1)^5 dx")
        titles = [s.title for s in sol.steps]
        self.assertTrue(any("Değişken değiştirme" in t for t in titles))
        self.assertTrue(any("integrali" in t for t in titles))

    def test_definite_integral_theorem_step(self):
        sol = self._ask("integral of x^2 from 1 to 2")
        titles = [s.title for s in sol.steps]
        self.assertTrue(any("ana teoremi" in t for t in titles))
        self.assertEqual(sol.result, sp.Rational(7, 3))

    def test_limit_zero_over_zero_simplification(self):
        sol = self._ask("limit of (x^2-4)/(x-2) as x->2")
        titles = [s.title for s in sol.steps]
        self.assertIn("0/0 belirsizliği", titles)
        self.assertTrue(any("sadeleştir" in t for t in titles))
        self.assertEqual(sol.result, 4)

    def test_limit_degree_rule_at_infinity(self):
        sol = self._ask("limit of (3*x+1)/x as x->inf")
        titles = [s.title for s in sol.steps]
        self.assertIn("Sonsuzda derece kuralı", titles)
        self.assertEqual(sol.result, 3)


class TestDefiniteNotebookSteps(unittest.TestCase):
    def setUp(self):
        self.engine = MathPad()

    def test_dx_over_expr_notation(self):
        sol = self.engine.ask("integral of dx/(5x+1) from 0 to 1")
        self.assertEqual(sp.simplify(sp.sympify(sol.result) - sp.log(6) / 5), 0)
        titles = [step.title for step in sol.steps]
        self.assertTrue(any("Değişken değiştirme" in t for t in titles))
        self.assertTrue(any("Alt sınır" in t for t in titles))
        self.assertTrue(any("Üst sınır" in t for t in titles))
        self.assertTrue(any("sadeleştir" in t for t in titles))

    def test_fraction_upper_bound(self):
        sol = self.engine.ask("integral of dx/(x^2+1) from 0 to pi/4")
        self.assertEqual(sp.simplify(sp.sympify(sol.result) - sp.atan(sp.pi / 4)), 0)

    def test_fraction_lower_bound(self):
        sol = self.engine.ask("integral of dx/(3*x+2) from 0 to 2/3")
        result = sp.simplify(sp.sympify(sol.result))
        self.assertEqual(sp.simplify(result - sp.log(2) / 3), 0)

    def test_bounds_not_regressed(self):
        self.assertEqual(self.engine.ask("integral of x^2 from 0 to 3").result, 9)
        self.assertEqual(
            self.engine.ask("sin(x) fonksiyonunun 0 dan pi ye integrali").result, 2
        )


class TestTurkmen(unittest.TestCase):
    def setUp(self):
        self.engine = MathPad()

    def test_turkmen_denleme_solved(self):
        sol = self.engine.ask("deňlemäni çöz: 3x + 4 = 10")
        self.assertEqual(sol.solver, "algebra")
        self.assertEqual(sol.result, [{sp.Symbol("x"): 2}])

    def test_turkmen_ascii_denleme(self):
        sol = self.engine.ask("2x - 7 = 3 denlemani coz")
        self.assertEqual(sol.result, [{sp.Symbol("x"): 5}])

    def test_turkmen_derivative_with_special_chars(self):
        sol = self.engine.ask("x^2 fonksiyoniniň hosylayyşyny al")
        self.assertEqual(sol.solver, "calculus")
        self.assertEqual(sol.result, 2 * sp.Symbol("x"))

    def test_turkmen_derivative_ascii(self):
        sol = self.engine.ask("sin(x) hosylayysyny al")
        self.assertEqual(sol.result, sp.cos(sp.Symbol("x")))

    def test_turkmen_statistics_jemi(self):
        sol = self.engine.ask("jemi [10, 20, 30]")
        self.assertEqual(sol.result_text, "60")

    def test_fold_turkmen(self):
        from mathpad.utils import fold_turkmen

        self.assertEqual(fold_turkmen("deňlemäni"), "denlemani")
        self.assertEqual(fold_turkmen("hosylaýyş"), "hosylayys")


if __name__ == "__main__":
    unittest.main()
