"""Claude 2. tur inceleme listesi: hata maddeleri + kabul listesi kontrolu.

Her hata maddesi ve kabul listesindeki her soru icin birim test; ondalik
yaklasim kullanilmaz, kesin degerler dogrulanir.
"""

import unittest

import sympy as sp

from mathpad import MathPad
from mathpad.engine import NoSolverFound

X = sp.Symbol("x")
DX = sp.Symbol("dx")


def _same(result, expected):
    result = sp.sympify(result)
    expected = sp.sympify(expected)
    if isinstance(result, sp.Set) or isinstance(expected, sp.Set):
        return result == expected
    if isinstance(result, sp.Eq) or isinstance(expected, sp.Eq):
        return result == expected
    return sp.simplify(result - expected) == 0


class ClaudeRound2Tests(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _ask(self, question):
        return self.pad.ask(question)

    # ------------------------------------------------------------ 1. yanlis cevap
    def test_abs_derivative_pipe_form(self):
        sol = self._ask("d/dx |x|")
        self.assertEqual(sol.result, sp.sign(sp.Symbol("x", real=True)))

    def test_abs_derivative_shift_pipe(self):
        sol = self._ask("d/dx |2x-3|")
        real_x = sp.Symbol("x", real=True)
        self.assertEqual(sol.result, 2 * sp.sign(2 * real_x - 3))

    def test_multi_log_equation(self):
        sol = self._ask("log_2(x)+log_2(x-2)=3")
        self.assertEqual(sol.result, [{X: 4}])

    def test_remainder_polynomial_form(self):
        self.assertEqual(
            self._ask("x^3-4x^2+x+6 polinomu x+1 ile bölündüğünde kalan").result, 0)
        self.assertEqual(
            self._ask("x^3-4x^2+x+6 polinomu x-1 ile bölündüğünde kalan").result, 4)

    def test_abs_inequality_ge(self):
        sol = self._ask("|2x+1|>=5")
        expected = sp.Union(sp.Interval(-sp.oo, -3), sp.Interval(2, sp.oo))
        self.assertEqual(sol.simplify() if hasattr(sol, "simplify") else sol.result, expected)

    def test_exponential_real_roots_only(self):
        self.assertEqual(self._ask("2^(2x)=64").result, [{X: 3}])
        self.assertTrue(
            all(s[X].is_real for s in self._ask("4^x=64").result if X in s))

    # ------------------------------------------------- 2. cop ureten girisler
    def test_differential_spellings(self):
        expected = (2 * X * sp.sin(X) + X**2 * sp.cos(X)) * DX
        for wording in (
            "f(x)=x^2*sin(x) diferensialyny tapyn",
            "f(x)=x^2*sin(x) diferensiyalyny tapyn",
            "f(x)=x^2*sin(x) diferensialyn tapyn",
        ):
            sol = self._ask(wording)
            self.assertEqual(sol.solver, "calculus")
            self.assertEqual(sp.simplify(sol.result - expected), 0)

    def test_second_derivative_turkmen_onum(self):
        sol = self._ask("f(x)=x^4-4x^2 ikinji önüm")
        self.assertEqual(sp.simplify(sp.expand(sol.result) - 12 * X**2 + 8), 0)

    def test_progression_without_keyword(self):
        self.assertEqual(self._ask("a1=5, d=3, a20").result, 62)
        self.assertEqual(self._ask("a_1=5, d=3, S_10").result, 185)
        self.assertEqual(self._ask("b1=3, q=2, b6").result, 96)
        self.assertEqual(self._ask("b1=3, q=2, S_6").result, 189)

    def test_binomial_expand_request(self):
        sol = self._ask("(2x-1)^3 ifadesini aç")
        self.assertEqual(sp.expand(sol.result - 8 * X**3 + 12 * X**2 - 6 * X + 1), 0)

    def test_abs_inequality_with_word(self):
        sol = self._ask("|x-4|<3 eşitsizliğini çöz")
        self.assertEqual(sol.solver, "advanced_algebra")
        self.assertEqual(sol.result, sp.Interval.open(1, 7))

    # ------------------------------------------------------ 3. sinirlarda eksik
    def test_undirected_limit_explicit(self):
        sol = self._ask("lim x->0 1/x")
        self.assertIn("mevcut değil", str(sol.result))
        sol = self._ask("lim x->0+ 1/x")
        self.assertEqual(sol.result, sp.oo)

    def test_divergent_integral(self):
        sol = self._ask("integral of 1/x from -1 to 1")
        self.assertIn("Iraksak", str(sol.result))

    def test_area_single_curve_vertical_bound(self):
        self.assertEqual(
            self._ask("y=sqrt(x), y=0, x=4 meydany").result, sp.Rational(16, 3))

    def test_area_with_pi_constant_bound(self):
        self.assertEqual(
            self._ask("y=sin(x), y=0, x=0, x=pi meydany").result, 2)

    # ------------------------------------------------------------- genel kural
    def test_unknown_word_gives_explicit_error(self):
        with self.assertRaises((NoSolverFound, ValueError)):
            self.pad.ask("gokkusag(x)+3=2 denklemini tapyň")

    def test_algebra_rejects_long_unknown_symbols(self):
        sol = self.pad.ask("f(x)=3x^3+cos(2x)-3 differensialyny tapyn")
        self.assertEqual(sol.solver, "calculus")
        self.assertNotEqual(sol.solver, "algebra")


class AcceptanceAlgebraTests(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _check(self, question, expected):
        sol = self.pad.ask(question)
        self.assertTrue(
            _same(sol.result, expected),
            f"{question!r}: {sol.result} != {expected}")

    def _roots(self, question):
        sol = self.pad.ask(question)
        return {d[sp.Symbol("x")] for d in sol.result}

    def test_01_quadratic(self):
        self.assertEqual(self._roots("3x^2-7x+2=0"), {2, sp.Rational(1, 3)})

    def test_02_complex_roots(self):
        self.assertEqual(self._roots("x^2+4x+5=0"), {-2 - sp.I, -2 + sp.I})

    def test_03_quadratic_inequality(self):
        self._check("x^2-2x-15>0",
                    sp.Union(sp.Interval.open(-sp.oo, -3), sp.Interval.open(5, sp.oo)))

    def test_04_linear_system(self):
        sol = self.pad.ask("2x+3y=12, x-y=1")
        self.assertEqual(sol.result, [{sp.Symbol("x"): 3, sp.Symbol("y"): 2}])

    def test_05_abs_ineq_lt(self):
        self._check("|x-4|<3", sp.Interval.open(1, 7))

    def test_06_abs_ineq_ge(self):
        self._check("|2x+1|>=5",
                    sp.Union(sp.Interval(-sp.oo, -3), sp.Interval(2, sp.oo)))

    def test_07_log_equation(self):
        self.assertEqual(self.pad.ask("log_3(x-1)=2").result, [{X: 10}])

    def test_08_exp_equation(self):
        self.assertEqual(self.pad.ask("2^(2x)=64").result, [{X: 3}])

    def test_09_radical(self):
        self.assertEqual(self.pad.ask("sqrt(2x+3)=x").result, [3])

    def test_10_factorization(self):
        sol = self.pad.ask("x^4-16 çarpanlarına ayır")
        self.assertEqual(sp.expand(sol.result), sp.expand((X - 2) * (X + 2) * (X**2 + 4)))

    def test_11_simplify(self):
        sol = self.pad.ask("(x^2-1)/(x^2-x-2) sadeleştir")
        self.assertEqual(sp.simplify(sp.expand(sol.result * (X - 2)) - (X - 1)), 0)

    def test_12_arithmetic_progression(self):
        self.assertEqual(self.pad.ask("a1=5, d=3, a20").result, 62)

    def test_13_arithmetic_sum(self):
        self.assertEqual(self.pad.ask("a_1=5, d=3, S_10").result, 185)

    def test_14_geometric_term(self):
        self.assertEqual(self.pad.ask("b1=3, q=2, b6").result, 96)

    def test_15_geometric_sum(self):
        self.assertEqual(self.pad.ask("b1=3, q=2, S_6").result, 189)

    def test_16_vieta_ratio(self):
        self.assertEqual(self.pad.ask("x^2-5x+3=0 için 1/x1+1/x2").result, sp.Rational(5, 3))

    def test_17_complex_division(self):
        self.assertEqual(self.pad.ask("(3+i)/(1-i)").result, 1 + 2 * sp.I)

    def test_18_binomial_expand(self):
        sol = self.pad.ask("(2x-1)^3 ifadesini aç")
        self.assertEqual(sp.expand(sol.result),
                         sp.expand(8 * X**3 - 12 * X**2 + 6 * X - 1))

    def test_19_remainder_plus(self):
        self.assertEqual(
            self.pad.ask("x^3-4x^2+x+6 polinomu x+1 ile bölündüğünde kalan").result, 0)

    def test_20_remainder_minus(self):
        self.assertEqual(
            self.pad.ask("x^3-4x^2+x+6 polinomu x-1 ile bölündüğünde kalan").result, 4)

    def test_21_multi_log(self):
        self.assertEqual(self.pad.ask("log_2(x)+log_2(x-2)=3").result, [{X: 4}])

    def test_22_exp_power(self):
        self.assertEqual(self.pad.ask("5^x=125").result, [{X: 3}])

    def test_23_system_with_circle(self):
        sol = self.pad.ask("x^2+y^2=25, x+y=7")
        pairs = {(d[sp.Symbol("x")], d[sp.Symbol("y")]) for d in sol.result}
        self.assertEqual(pairs, {(3, 4), (4, 3)})


class AcceptanceAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _check(self, question, expected):
        sol = self.pad.ask(question)
        self.assertTrue(
            _same(sol.result, expected),
            f"{question!r}: {sol.result} != {expected}")

    def test_01_limit_exp(self):
        self._check("lim x->0 (e^(3x)-1)/x", 3)

    def test_02_limit_infinity(self):
        self._check("lim x->inf (3x^2+x)/(x^2+5)", 3)

    def test_03_limit_cubic(self):
        self._check("lim x->1 (x^3-1)/(x-1)", 3)

    def test_04_limit_undefined(self):
        sol = self.pad.ask("lim x->0 1/x")
        self.assertIn("mevcut değil", str(sol.result))

    def test_05_abs_derivative(self):
        self._check("d/dx |x|", sp.sign(sp.Symbol("x", real=True)))

    def test_06_product_derivative(self):
        self._check("d/dx x*sin(x)", sp.sin(X) + X * sp.cos(X))

    def test_07_log_derivative(self):
        self._check("d/dx ln(x^2+1)", 2 * X / (X**2 + 1))

    def test_08_quotient_derivative(self):
        self._check("d/dx x^2/(x+1)", (X**2 + 2 * X) / (X + 1)**2)

    def test_09_exp_cos_derivative(self):
        self._check("d/dx e^(3x)*cos(x)", sp.exp(3 * X) * (3 * sp.cos(X) - sp.sin(X)))

    def test_10_sqrt_derivative(self):
        self._check("d/dx sqrt(x^2+1)", X / sp.sqrt(X**2 + 1))

    def test_11_extremum(self):
        sol = self.pad.ask("f(x)=x^3-6x^2+9x-1 ekstremum")
        text = str(sol.result)
        self.assertIn("f = 3", text)
        self.assertIn("f = -1", text)

    def test_12_tangent_line(self):
        sol = self.pad.ask("y=x^3-x eğrisine x0=2 teğet")
        y = sp.Symbol("y")
        self.assertEqual(sol.result, sp.Eq(y, 11 * X - 16))

    def test_13_max_min_interval(self):
        sol = self.pad.ask("f(x)=x^3-3x+1 [0;2] en büyük en küçük")
        self.assertIn("3", str(sol.result))
        self.assertIn("-1", str(sol.result))

    def test_14_integral_xex(self):
        self._check("integral of x*e^x dx", (X - 1) * sp.exp(X))

    def test_15_integral_x2lnx(self):
        self._check("integral of x^2*ln(x) dx", X**3 * sp.log(X) / 3 - X**3 / 9)

    def test_16_integral_arctan(self):
        self._check("integral of 1/(x^2+1) from 0 to 1", sp.pi / 4)

    def test_17_integral_cos2(self):
        self._check("integral of cos^2(x) from 0 to pi", sp.pi / 2)

    def test_18_integral_polynomial(self):
        self._check("integral of 3x^2-2x+1 from 1 to 3", 20)

    def test_19_divergent(self):
        sol = self.pad.ask("integral of 1/x from -1 to 1")
        self.assertIn("Iraksak", str(sol.result))

    def test_20_area_parabola_line(self):
        self._check("y=x^2, y=x+2 sinirli alan", sp.Rational(9, 2))

    def test_21_area_sqrt(self):
        self._check("y=sqrt(x), y=0, x=4 meydany", sp.Rational(16, 3))

    def test_22_area_sine(self):
        self._check("y=sin(x), y=0, x=0, x=pi meydany", 2)

    def test_23_differential(self):
        self._check("f(x)=x^2*sin(x) diferensialyny tapyn",
                    (2 * X * sp.sin(X) + X**2 * sp.cos(X)) * DX)

    def test_24_differential_log(self):
        self._check("f(x)=2x^3-ln(x) diferensialyny tapyn",
                    (6 * X**2 - 1 / X) * DX)

    def test_25_differential_exp(self):
        self._check("f(x)=e^(2x)+x^2 diferensialyny tapyn",
                    (2 * sp.exp(2 * X) + 2 * X) * DX)


if __name__ == "__main__":
    unittest.main()
