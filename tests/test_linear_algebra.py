import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad
from mathpad.solvers import LinearAlgebraSolver

import sympy as sp


class TestLinearAlgebra(unittest.TestCase):
    def setUp(self):
        self.solver = LinearAlgebraSolver()
        self.engine = MathPad()

    def solve(self, question):
        return self.solver.solve(question)

    def test_determinant_2x2(self):
        solution = self.solve("[[1,2],[3,4]] matrisinin determiniantı")
        self.assertEqual(solution.result, -2)

    def test_sarrus_step_exists(self):
        solution = self.solve("[[1,2],[3,4]] determinanti")
        titles = [s.title for s in solution.steps]
        self.assertTrue(any("Sarrus" in t for t in titles))

    def test_determinant_3x3(self):
        solution = self.solve("[[2,0,1],[1,3,2],[1,1,2]] determinant")
        self.assertEqual(solution.result, 6)

    def test_singular_matrix_raises(self):
        with self.assertRaises(ValueError):
            self.solve("[[1,2],[2,4]] ters matris")

    def test_inverse(self):
        solution = self.solve("[[4,7],[2,6]] inverse")
        expected = sp.Matrix([[sp.Rational(3, 5), sp.Rational(-7, 10)],
                              [sp.Rational(-1, 5), sp.Rational(2, 5)]])
        self.assertTrue(solution.result == expected)

    def test_eigen_diagonal(self):
        solution = self.solve("[[2,0],[0,3]] özdeğerleri")
        self.assertEqual(set(solution.result["özdeğerler"]), {2, 3})

    def test_eigenvectors_exist(self):
        solution = self.solve("[[2,0],[0,3]] özvektörlerini bul")
        self.assertGreater(len(solution.result["özvektörler"]), 0)

    def test_multiply(self):
        solution = self.solve("[[1,2],[3,4]] [[5,6],[7,8]] çarpımı")
        expected = sp.Matrix([[19, 22], [43, 50]])
        self.assertEqual(solution.result, expected)

    def test_incompatible_multiply_raises(self):
        with self.assertRaises(ValueError):
            self.solve("[[1,2],[3,4]] [[1,2],[3,4],[5,6]] çarpımı")

    def test_trace(self):
        solution = self.solve("[[2,1],[1,3]] izi")
        self.assertEqual(solution.result, 5)

    def test_rank(self):
        solution = self.solve("[[1,2],[2,4]] rank")
        self.assertEqual(solution.result, 1)

    def test_routing_matrix(self):
        solution = self.engine.ask("[[1,2],[3,4]] matrisinin tersi")
        self.assertEqual(solution.solver, "linear_algebra")


if __name__ == "__main__":
    unittest.main()
