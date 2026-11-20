import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad, NoSolverFound, Notebook, Solution, Step
from mathpad.solvers.base import Solver


class AlwaysSolver(Solver):
    name = "always"
    title = "Her Şey"

    def can_handle(self, question: str) -> float:
        return 0.99

    def solve(self, question: str) -> Solution:
        return Solution(
            question=question, solver=self.name, title="test",
            result=42, result_tex="42", result_text="42",
        )


class NeverSolver(Solver):
    name = "never"
    title = "Hiçbir Şey"

    def can_handle(self, question: str) -> float:
        return 0.1

    def solve(self, question: str) -> Solution:
        raise ValueError("çözülemedi")


class BrokenSolver(Solver):
    name = "broken"
    title = "Hatalı"

    def can_handle(self, question: str) -> float:
        return 1.0

    def solve(self, question: str) -> Solution:
        raise ZeroDivisionError


class TestEngine(unittest.TestCase):
    def test_fallback_to_second_choice(self):
        engine = MathPad(solvers=(BrokenSolver(), AlwaysSolver()), threshold=0.5)
        solution = engine.ask("herhangi bir soru")
        self.assertEqual(solution.solver, "always")

    def test_no_solver_raises(self):
        engine = MathPad(solvers=(NeverSolver(),), threshold=0.5)
        with self.assertRaises(NoSolverFound):
            engine.ask("merhaba dünya")

    def test_empty_question_raises(self):
        engine = MathPad()
        with self.assertRaises(NoSolverFound):
            engine.ask("   ")

    def test_history_records(self):
        engine = MathPad(solvers=(AlwaysSolver(),), threshold=0.5)
        engine.ask("soru 1")
        engine.ask("soru 2")
        self.assertEqual(len(engine.history), 2)
        self.assertEqual(engine.history[0].question, "soru 1")

    def test_register_new_solver(self):
        engine = MathPad()
        custom = AlwaysSolver()
        engine.register(custom)
        self.assertIn(custom, engine.solvers)


class TestNotebook(unittest.TestCase):
    def _solution(self, question: str) -> Solution:
        return Solution(
            question=question,
            solver="test",
            title="Test çözümü",
            result="test",
            result_tex="x^2 + 1",
            result_text="x**2 + 1",
            steps=[
                Step("ilk adım", content="a"),
                Step("ikinci adım", latex="\\frac{1}{2}"),
            ],
        )

    def test_markdown_contains_latex_and_question(self):
        notebook = Notebook()
        notebook.add(self._solution("x + 1 = 2?"))
        md = notebook.markdown()
        self.assertIn("$x^2 + 1$", md.replace("$$", "$"))
        self.assertIn("**Soru:** x + 1 = 2?", md)
        self.assertIn("\\frac{1}{2}", md)

    def test_html_contains_mathjax(self):
        notebook = Notebook(title="Deneme")
        notebook.add(self._solution("soru"))
        html = notebook.html()
        self.assertIn("MathJax", html)
        self.assertIn("Deneme", html)
        self.assertIn("x^2 + 1", html)

    def test_text_output(self):
        notebook = Notebook()
        notebook.add(self._solution("soru metni"))
        plain = notebook.text()
        self.assertIn("soru metni", plain)
        self.assertIn("x**2 + 1", plain)

    def test_save_files(self):
        notebook = Notebook()
        for i in range(3):
            notebook.add(self._solution(f"soru {i}"))
        with tempfile.TemporaryDirectory() as tmp:
            md = notebook.save_markdown(os.path.join(tmp, "d.md"))
            html = notebook.save_html(os.path.join(tmp, "d.html"))
            txt = notebook.save_text(os.path.join(tmp, "d.txt"))
            for path in (md, html, txt):
                self.assertTrue(os.path.exists(path))
                self.assertGreater(os.path.getsize(path), 100)


class TestCustomModuleImport(unittest.TestCase):
    def test_package_version(self):
        import mathpad
        self.assertTrue(hasattr(mathpad, "__version__"))

    def test_exports(self):
        import mathpad
        for name in ("MathPad", "Notebook", "Solution", "Step"):
            self.assertTrue(hasattr(mathpad, name))


if __name__ == "__main__":
    unittest.main()
