"""verify.py doğrulayıcı katmanı testleri."""

from __future__ import annotations

import unittest

import sympy as sp

from mathpad.verify import VerificationError, verify_derivative, verify_equations, verify_integral, verify_limit


class VerifyDerivativeTests(unittest.TestCase):
    def test_wrong_derivative_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_derivative({"expr": x**2, "var": x, "result": 2*x + 1})

    def test_correct_derivative_passes(self):
        x = sp.Symbol("x")
        verify_derivative({"expr": x**2, "var": x, "result": 2*x})

    def test_differential_dx_factor_stripped(self):
        x = sp.Symbol("x")
        verify_derivative({"expr": x**3, "var": x, "result": 3*x**2*sp.Symbol("dx")})


class VerifyIntegralTests(unittest.TestCase):
    def test_wrong_definite_integral_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_integral({"expr": x**2, "var": x, "bounds": (0, 3), "result": 8})

    def test_correct_definite_integral_passes(self):
        x = sp.Symbol("x")
        verify_integral({"expr": x**2, "var": x, "bounds": (0, 3), "result": 9})

    def test_wrong_antiderivative_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_integral({"expr": x**2, "var": x, "bounds": None, "result": x**3})


class VerifyLimitTests(unittest.TestCase):
    def test_wrong_limit_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_limit({"expr": sp.sin(x)/x, "var": x, "point": 0, "result": 2})

    def test_correct_limit_passes(self):
        x = sp.Symbol("x")
        verify_limit({"expr": sp.sin(x)/x, "var": x, "point": 0, "result": 1})

    def test_divergent_converged_mismatch_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_limit({"expr": 1/x, "var": x, "point": 0, "result": 5})


class VerifyEquationTests(unittest.TestCase):
    def test_wrong_root_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_equations({
                "equations": [sp.Eq(x**2 - 4, 0)],
                "conditions": [],
                "results": [{x: 3}],
            })

    def test_condition_violation_caught(self):
        x = sp.Symbol("x")
        with self.assertRaises(VerificationError):
            verify_equations({
                "equations": [sp.Eq(x**2 - 4, 0)],
                "conditions": [x > 0],
                "results": [{x: -2}],
            })

    def test_valid_solution_passes(self):
        x = sp.Symbol("x")
        verify_equations({
            "equations": [sp.Eq(x**2 - 4, 0)],
            "conditions": [x > 0],
            "results": [{x: 2}],
        })


if __name__ == "__main__":
    unittest.main()
