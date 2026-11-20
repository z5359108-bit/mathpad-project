import os
import shutil
import tempfile
import unittest

try:
    import matplotlib  # noqa: F401

    HAS_MPL = True
except ImportError:
    HAS_MPL = False

from mathpad import MathPad
from mathpad.rendering.png import solution_to_png


@unittest.skipUnless(HAS_MPL, "matplotlib kurulu değil")
class TestPngRendering(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = MathPad()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_quadratic_renders_png(self):
        path = solution_to_png(self.engine.ask("x^2 - 3x + 2 = 0"), os.path.join(self.tmp, "a.png"))
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 1000)

    def test_various_solvers_render(self):
        questions = [
            "integral of x^2 from 0 to 3",
            "[[1,2],[3,4]] matrisinin determinantı",
            "360 sayısını asal çarpanlarına ayır",
            "varyans [2, 4, 4, 4, 5, 5, 7, 9]",
        ]
        for i, q in enumerate(questions, 1):
            p = solution_to_png(self.engine.ask(q), os.path.join(self.tmp, f"s{i}.png"))
            self.assertTrue(os.path.isfile(p) and os.path.getsize(p) > 1000)


if __name__ == "__main__":
    unittest.main()
