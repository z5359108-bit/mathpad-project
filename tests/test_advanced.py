"""Kullanicinin defter orneklerinden olusan ileri cebir/analiz test serisi.

A serisi: Cebir (20 soru), B serisi: Analiz (20 soru).
Her test sorunun sonucunu dogrular; birkaci adim basliklarini da kontrol eder.
"""

import unittest

import sympy as sp

from mathpad import MathPad


class TestAlgebraSeries(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _ask(self, question):
        return self.pad.ask(question)

    def test_a1_quadratic(self):
        sol = self._ask("2x^2-5x+2=0")
        self.assertEqual(sorted(r[sp.Symbol("x")] for r in sol.result), [sp.Rational(1, 2), 2])

    def test_a2_inequality_interval(self):
        sol = self._ask("x^2-7x+12<=0")
        self.assertEqual(sol.result, sp.Interval(3, 4))

    def test_a3_system(self):
        sol = self._ask("x+y=5 ; x-y=1")
        self.assertEqual(sol.result, [{sp.Symbol("x"): 3, sp.Symbol("y"): 2}])

    def test_a4_absolute_value(self):
        sol = self._ask("|2x-3|=7")
        self.assertEqual(sol.result, [-2, 5])

    def test_a5_log_equation(self):
        sol = self._ask("log_2(x+3)=4")
        self.assertEqual(sol.result, [{sp.Symbol("x"): 13}])

    def test_a6_exp_equation(self):
        sol = self._ask("3^(x+1)=81")
        self.assertEqual(sol.result, [{sp.Symbol("x"): 3}])

    def test_a7_radical_equation(self):
        sol = self._ask("sqrt(x+5)=x-1")
        self.assertEqual(sol.result, [4])

    def test_a8_arithmetic_progression(self):
        sol = self._ask("Arifmetik progressiya: a_1=3, d=4, S_10=?")
        self.assertEqual(sol.result, 210)

    def test_a9_geometric_progression(self):
        sol = self._ask("Geometrik progressiya: b_1=2, q=3, b_5=?")
        self.assertEqual(sol.result, 162)

    def test_a10_vieta(self):
        sol = self._ask("x^2-6x+5=0 denkleminin kokleri x_1 ve x_2 olsun, x_1^2+x_2^2 kacadir")
        self.assertEqual(sol.result, 26)

    def test_a11_simplify(self):
        sol = self._ask("sadelestir (x^2-9)/(x-3)")
        self.assertEqual(sp.expand(sol.result - (sp.Symbol("x") + 3)), 0)

    def test_a12_factor(self):
        sol = self._ask("x^3-8 carpanlarina ayir")
        self.assertEqual(sp.expand(sol.result - (sp.Symbol("x") - 2) * (sp.Symbol("x") ** 2 + 2 * sp.Symbol("x") + 4)), 0)

    def test_a13_sum_product_identity(self):
        sol = self._ask("a+b=5, ab=6 ise a^2+b^2 kacadir")
        self.assertEqual(sol.result, 13)

    def test_a14_remainder_theorem(self):
        sol = self._ask("P(x)=x^3-2x+5 polinomunu x-2 ile bolundugunde kalan kactir")
        self.assertEqual(sol.result, 9)

    def test_a15_complex_product(self):
        sol = self._ask("(1+2i)(3-i)=?")
        self.assertEqual(sp.simplify(sol.result - (5 + 5 * sp.I)), 0)

    def test_a16_complex_modulus(self):
        sol = self._ask("|3+4i|=?")
        self.assertEqual(sol.result, 5)

    def test_a17_linear_inequality(self):
        sol = self._ask("2x-3>5x+6")
        self.assertEqual(sol.result, sp.Interval.open(-sp.oo, -3))

    def test_a18_log_evaluation(self):
        sol = self._ask("log_3(27)+log_2(8) kactir")
        self.assertEqual(sol.result, 6)

    def test_a19_rational_inequality(self):
        sol = self._ask("(x-1)/(x+2)>=0")
        expected = sp.Union(sp.Interval.open(-sp.oo, -2), sp.Interval(1, sp.oo))
        self.assertEqual(sp_extended(sol.result), sp_extended(expected))

    def test_a20_binomial_coefficient(self):
        sol = self._ask("(x+2)^4 aciliminda x^2'nin katsayisi kactir")
        self.assertEqual(sol.result, 24)


def sp_extended(value):
    return value


class TestAnalysisSeries(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()
        self.x = sp.Symbol("x")

    def _ask(self, question):
        return self.pad.ask(question)

    def test_b1_limit_factor_cancel(self):
        sol = self._ask("limit of (x^2-4)/(x-2) as x->2")
        self.assertEqual(sol.result, 4)

    def test_b2_standard_trig_limit(self):
        sol = self._ask("limit of sin(3x)/x as x->0")
        self.assertEqual(sol.result, 3)

    def test_b3_limit_at_infinity(self):
        sol = self._ask("limit of (2x^2+1)/(x^2-3) as x->oo")
        self.assertEqual(sol.result, 2)

    def test_b4_standard_exp_limit(self):
        sol = self._ask("limit of (e^x-1)/x as x->0")
        self.assertEqual(sol.result, 1)

    def test_b5_product_derivative(self):
        sol = self._ask("f(x)=x^3*ln(x) fonksiyonunun turevi")
        self.assertEqual(sp.simplify(sol.result - (3 * self.x**2 * sp.log(self.x) + self.x**2)), 0)

    def test_b6_quotient_rule(self):
        sol = self._ask("f(x)=(x^2+1)/(x-1) fonksiyonunun turevi")
        expected = (self.x**2 - 2 * self.x - 1) / (self.x - 1) ** 2
        self.assertEqual(sp.simplify(sol.result - expected), 0)
        self.assertIn("Ortak paydaya getir", [s.title for s in sol.steps])

    def test_b7_sin_squared(self):
        sol = self._ask("f(x)=sin(x)^2 fonksiyonunun turevi")
        self.assertEqual(sp.simplify(sol.result - sp.sin(2 * self.x)), 0)
        self.assertIn("Trigonometrik özdeşlik", [s.title for s in sol.steps])

    def test_b8_chain_exp(self):
        sol = self._ask("f(x)=exp(x^2) fonksiyonunun turevi")
        self.assertEqual(sp.simplify(sol.result - 2 * self.x * sp.exp(self.x**2)), 0)

    def test_b9_chain_log(self):
        sol = self._ask("f(x)=ln(x^2+1) fonksiyonunun turevi")
        self.assertEqual(sp.simplify(sol.result - 2 * self.x / (self.x**2 + 1)), 0)

    def test_b10_tangent_line(self):
        sol = self._ask("y=x^2+1 egrisinin x_0=1 noktasindaki tegeti")
        self.assertEqual(sp.simplify(sol.result.rhs - 2 * self.x), 0)

    def test_b11_extrema(self):
        sol = self._ask("f(x)=x^3-3x fonksiyonunun ekstremumlari")
        text = str(sol.result)
        self.assertIn("x = -1", text)
        self.assertIn("f = 2", text)
        self.assertIn("x = 1", text)
        self.assertIn("f = -2", text)

    def test_b12_closed_interval(self):
        sol = self._ask("f(x)=x^2-4x+1 fonksiyonunun [0;3] araliginda en buyuk ve en kucuk degeri")
        text = str(sol.result)
        self.assertIn("max f = 1", text)
        self.assertIn("min f = -3", text)

    def test_b13_indefinite_integral_poly(self):
        sol = self._ask("integral of 3x^2-4x+5 dx")
        self.assertEqual(sp.diff(sol.result, self.x), 3 * self.x**2 - 4 * self.x + 5)

    def test_b14_indefinite_integral_mix(self):
        sol = self._ask("integral of (1/x + e^x) dx")
        self.assertEqual(sp.diff(sp.simplify(sol.result), self.x) - (1 / self.x + sp.exp(self.x)), 0)

    def test_b15_u_substitution(self):
        sol = self._ask("integral of x*exp(x^2) from 0 to 1")
        self.assertEqual(sp.simplify(sol.result - (sp.E - 1) / 2), 0)

    def test_b16_by_parts_log(self):
        sol = self._ask("integral of ln(x) from 1 to e")
        self.assertEqual(sol.result, 1)

    def test_b17_by_parts_product(self):
        sol = self._ask("integral of x*cos(x) dx")
        self.assertEqual(sp.simplify(sol.result - (self.x * sp.sin(self.x) + sp.cos(self.x))), 0)

    def test_b18_half_angle(self):
        sol = self._ask("integral of sin(x)^2 from 0 to pi/2")
        self.assertEqual(sp.simplify(sol.result - sp.pi / 4), 0)

    def test_b19_area_between_curves(self):
        sol = self._ask("y=x^2 ve y=x^3 egrileriyle sinirli alani hesapla")
        self.assertEqual(sp.simplify(sol.result - sp.Rational(1, 12)), 0)

    def test_b20_second_derivative(self):
        sol = self._ask("f(x)=x^4-2x^3 fonksiyonunun ikinci turevi")
        self.assertEqual(sp.expand(sol.result - (12 * self.x**2 - 12 * self.x)), 0)

    def test_b20_turkmen_variant(self):
        sol = self._ask("f(x)=x^4-2x^3 funksiyanyn ikinji onumi")
        self.assertEqual(sp.expand(sol.result - (12 * self.x**2 - 12 * self.x)), 0)


if __name__ == "__main__":
    unittest.main()
