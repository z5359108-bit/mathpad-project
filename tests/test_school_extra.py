"""P3 paketi: school_extra aileleri (ters trigonometrik, |f|=|g|,
tanım kümesi, ters fonksiyon, f(g(x)), artan/azalan, dönüm noktası,
polinom bölme), kisa dispatch ve doğrulayıcı testleri.
"""

import unittest

import sympy as sp

from mathpad import MathPad
from mathpad.rendering.defter import defter_metni
from mathpad.rendering.kisa import kisa_satirlar
from mathpad.solvers.school_extra import SchoolExtraSolver
from mathpad.verify import verify_solution

x = sp.Symbol("x")


class TestInverseTrig(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_arcsin_half(self):
        sol = self.pad.ask("arcsin(1/2)")
        self.assertEqual(sol.result, sp.pi / 6)
        self.assertEqual(sol.solver, "school_extra")

    def test_arccos_half(self):
        self.assertEqual(self.pad.ask("arccos(1/2)").result, sp.pi / 3)

    def test_arctan_one(self):
        self.assertEqual(self.pad.ask("arctan(1)").result, sp.pi / 4)

    def test_arctan_sqrt3(self):
        self.assertEqual(self.pad.ask("arctan(sqrt(3))").result, sp.pi / 3)

    def test_arcsin_minus1(self):
        self.assertEqual(self.pad.ask("arcsin(-1)").result, -sp.pi / 2)

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("arcsin(1/2)"))
        self.assertEqual(satirlar, ["arcsin(1/2) = \u03c0/6"])

    def test_derivative_not_captured(self):
        sol = self.pad.ask("d/dx arctan(x)")
        self.assertEqual(sp.simplify(sol.result - 1 / (x ** 2 + 1)), 0)


class TestAbsAbs(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_simple(self):
        sol = self.pad.ask("|x-1|=|x+1|")
        self.assertEqual(sol.result, [{x: 0}])
        self.assertEqual(sol.solver, "school_extra")

    def test_two_roots(self):
        sol = self.pad.ask("|2x-3|=|x+1|")
        self.assertEqual(sol.result, [{x: sp.Rational(2, 3)}, {x: 4}])

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("|2x-3|=|x+1|"))
        self.assertEqual(satirlar, ["(2x \u2212 3)\u00b2 = (x + 1)\u00b2", "x = 2/3, x = 4"])


class TestDomain(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_kok(self):
        sol = self.pad.ask("tanım kümesi y = sqrt(x-2)")
        self.assertEqual(sol.result, sp.Interval(2, sp.oo))
        self.assertEqual(sol.solver, "school_extra")

    def test_payda(self):
        beklenen = sp.Union(sp.Interval.open(-sp.oo, 3), sp.Interval.open(3, sp.oo))
        self.assertEqual(self.pad.ask("tanım kümesi y = 1/(x-3)").result, beklenen)

    def test_log(self):
        self.assertEqual(
            self.pad.ask("tanım kümesi y = ln(x-1)").result, sp.Interval.open(1, sp.oo))

    def test_polynomial_reals(self):
        self.assertEqual(self.pad.ask("tanım kümesi y = 2x+3").result, sp.S.Reals)

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("tanım kümesi y = sqrt(x-2)"))
        self.assertEqual(satirlar, ["x \u2208 [2; +\u221e)"])

    def test_kisa_reals(self):
        satirlar = kisa_satirlar(self.pad.ask("tanım kümesi y = 2x+3"))
        self.assertEqual(satirlar, ["x \u2208 \u211d"])


class TestInverseFunction(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_linear(self):
        sol = self.pad.ask("ters fonksiyon y = 2x+3")
        self.assertEqual(sp.simplify(sol.result.rhs - (x - 3) / 2), 0)
        self.assertEqual(sol.solver, "school_extra")

    def test_cubic(self):
        sol = self.pad.ask("y = x^3 + 2 funksiyanyn tersini tap")
        fark = sp.simplify(((x - 2) ** sp.Rational(1, 3)) ** 3 + 2 - x)
        self.assertEqual(sp.simplify(fark), 0)

    def test_rational(self):
        sol = self.pad.ask("ters fonksiyon y = (2x+1)/3")
        self.assertEqual(sp.simplify(sol.result.rhs - (3 * x - 1) / 2), 0)

    def test_no_inverse_loud(self):
        with self.assertRaises(Exception):
            self.pad.ask("ters fonksiyon y = x^2")

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("ters fonksiyon y = 2x+3"))
        self.assertEqual(satirlar, ["f\u207b\u00b9(x) = (x \u2212 3)/2"])


class TestComposition(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_simple(self):
        sol = self.pad.ask("f(g(x)) if f(x)=x^2, g(x)=x+1")
        self.assertEqual(sol.result, x ** 2 + 2 * x + 1)
        self.assertEqual(sol.solver, "school_extra")

    def test_swapped(self):
        sol = self.pad.ask("f(g(x)) bul f(x)=2x+1, g(x)=x^2-3")
        self.assertEqual(sol.result, 2 * x ** 2 - 5)

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("f(g(x)) if f(x)=x^2, g(x)=x+1"))
        self.assertEqual(satirlar, ["f(g(x)) = x\u00b2 + 2x + 1"])


class TestMonotonicity(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_cubic(self):
        sol = self.pad.ask("artan azalan aralıklar x^3-3x")
        self.assertEqual(sol.solver, "school_extra")
        self.assertEqual(
            sol.result["artan"],
            sp.Union(sp.Interval.open(-sp.oo, -1), sp.Interval.open(1, sp.oo)))
        self.assertEqual(sol.result["azalan"], sp.Interval.open(-1, 1))

    def test_quartic(self):
        sol = self.pad.ask("artan azalan aralıklar x^4+2x^2")
        self.assertEqual(sol.result["artan"], sp.Interval.open(0, sp.oo))
        self.assertEqual(sol.result["azalan"], sp.Interval.open(-sp.oo, 0))

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("artan azalan aralıklar x^3-3x"))
        self.assertEqual(satirlar[0], "f\u2032(x) = 3x\u00b2 \u2212 3 = 0 \u21d2 x = \u00b11")
        self.assertEqual(satirlar[1], "artan x \u2208 (\u2212\u221e; \u22121) \u222a (1; +\u221e)")
        self.assertEqual(satirlar[2], "azalan x \u2208 (\u22121; 1)")


class TestInflection(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_cubic(self):
        sol = self.pad.ask("dönüm noktası x^3-3x")
        self.assertEqual(sol.result, [(0, 0)])
        self.assertEqual(sol.solver, "school_extra")

    def test_quartic(self):
        sol = self.pad.ask("dönüm noktası x^4-6x^2")
        self.assertEqual(sol.result, [(-1, -5), (1, -5)])

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("dönüm noktası x^3-3x"))
        self.assertEqual(satirlar, ["f\u2033(x) = 6x = 0 \u21d2 x = 0", "dönüm noktası (0; 0)"])


class TestPolynomialDivision(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def test_quotient_remainder(self):
        sol = self.pad.ask("x^3-2x+5 polinomunu x-2 ile böl")
        self.assertEqual(sol.result, (x ** 2 + 2 * x + 2, 9))
        self.assertEqual(sol.solver, "school_extra")

    def test_exact_division(self):
        sol = self.pad.ask("x^3-4x^2+x+6 polinomu x+1 ile böl")
        self.assertEqual(sol.result[1], 0)
        self.assertEqual(sol.result[0], x ** 2 - 5 * x + 6)

    def test_remainder_form_inverse_extended(self):
        sol = self.pad.ask("x^3-2x+5 polinomunu x-2 ile bölündüğünde kalan?")
        self.assertEqual(sol.result, 9)

    def test_kisa(self):
        satirlar = kisa_satirlar(self.pad.ask("x^3-2x+5 polinomunu x-2 ile böl"))
        self.assertEqual(
            satirlar, ["x\u00b3 \u2212 2x + 5 = (x \u2212 2)(x\u00b2 + 2x + 2) + 9"])


class TestVerifiers(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _verify(self, question):
        sol = self.pad.ask(question)
        verify_solution(sol)
        return sol

    def test_inverse_trig_verified(self):
        self._verify("arctan(1)")

    def test_abs_abs_verified(self):
        self._verify("|2x-3|=|x+1|")

    def test_domain_verified(self):
        self._verify("tanım kümesi y = sqrt(x-2)")
        self._verify("tanım kümesi y = 2x+3")

    def test_inverse_function_verified(self):
        self._verify("ters fonksiyon y = 2x+3")
        self._verify("y = x^3 + 2 funksiyanyn tersini tap")

    def test_composition_verified(self):
        self._verify("f(g(x)) bul f(x)=2x+1, g(x)=x^2-3")

    def test_monotonicity_verified(self):
        self._verify("artan azalan aralıklar x^3-3x")

    def test_inflection_verified(self):
        self._verify("dönüm noktası x^4-6x^2")

    def test_division_verified(self):
        self._verify("x^3-2x+5 polinomunu x-2 ile böl")

    def test_missing_root_caught(self):
        solver = SchoolExtraSolver()
        sol = solver.solve("|x|=|x+2|")
        bozuk = dict(sol.data)
        bozuk["roots"] = [0]
        with self.assertRaises(Exception):
            verify_solution(type("S", (), {"data": bozuk})())

    def test_unknown_pattern_loud(self):
        solver = SchoolExtraSolver()
        with self.assertRaises(Exception):
            solver.solve("tanım kümesi uydurma kelime xyz")

    def test_defter_no_raw_latex(self):
        sorular = [
            "arcsin(1/2)", "|2x-3|=|x+1|", "tanım kümesi y = sqrt(x-2)",
            "ters fonksiyon y = 2x+3", "f(g(x)) bul f(x)=x^2, g(x)=x+1",
            "artan azalan aralıklar x^3-3x", "dönüm noktası x^3-3x",
            "x^3-2x+5 polinomunu x-2 ile böl",
        ]
        for q in sorular:
            metin = defter_metni(self.pad.ask(q))
            yasak = ("\\frac", "\\Rightarrow", "\\quad", "\\left", "\\int",
                     "\\sqrt", "\\text", "\\cdot")
            for kelime in yasak:
                self.assertNotIn(kelime, metin, f"{q!r} defter çıktısında ham LaTeX var")


if __name__ == "__main__":
    unittest.main()
