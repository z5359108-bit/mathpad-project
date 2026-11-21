import json
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
from mathpad.rendering.png import chain_to_mathtext, defter_to_png, solution_to_png

GOLDEN = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "golden_defter.json",
)


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


@unittest.skipUnless(HAS_MPL, "matplotlib kurulu değil")
@unittest.skipUnless(os.path.isfile(GOLDEN), "golden_defter.json yok")
class TestDefterPngMathtext(unittest.TestCase):
    """Defter PNG'si render edilmiş formüllerle üretilmeli.

    Zincir satırları yapısal kaynaktan (defter_satirlar) gelir; PNG bu
    satırları mathtext'e çevirip çizer. Çevrilemeyen satır düz Unicode
    metin olarak kalır; ham LaTeX asla çıkmaz.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.engine = MathPad()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _golden_lines(self):
        with open(GOLDEN, encoding="utf-8") as fh:
            golden = json.load(fh)
        for item in golden:
            solution = self.engine.ask(item["soru"])
            from mathpad.rendering.defter import defter_satirlar

            yield item["soru"], defter_satirlar(solution)

    def test_golden_tum_satirlar_mathtext_e_cevrilir(self):
        for soru, lines in self._golden_lines():
            for line in lines:
                tex = chain_to_mathtext(line)
                self.assertIsNotNone(tex, f"mathtext'e çevrilemedi: {soru!r} -> {line!r}")

    def test_golden_defter_png_uretilir(self):
        for idx, (soru, _) in enumerate(self._golden_lines(), 1):
            solution = self.engine.ask(soru)
            p = defter_to_png(solution, os.path.join(self.tmp, f"d{idx:03d}.png"))
            self.assertTrue(os.path.isfile(p) and os.path.getsize(p) > 1000, soru)

    def test_kesirler_blok_ve_kumeler_korunur(self):
        cases = {
            "x₁,₂ = (5 ± 3)/4": ["\\frac{(5 \\pm 3)}{4}"],
            "S₁₀ = (2·3 + 9·4)/2 · 10 = 210": ["\\frac{(2", "9", ")}{2}", "\\cdot 10"],
            "(2x + 1)⁴/8 |₀¹ = 81/8": ["\\frac{(2x + 1)^{4}}{8}", "|_{0}^{1}"],
            "(x² − 2x − 1)/(x − 1)²": ["\\frac{(x^{2} - 2x - 1)}{(x - 1)^{2}}"],
            "x = 2ˣ⁻³": ["2^{x-3}"],
            "f⁻¹(x) = (x − 3)/2": ["f^{-1}(x)", "\\frac{(x - 3)}{2}"],
            "S = ∫₋₁¹ (1 − x⁴)dx": ["\\int_{-1}^{1}", "(1 - x^{4})"],
            "x ∈ (−∞; −3] ∪ [2; +∞)": ["\\in (-\\infty; -3] \\cup [2; +\\infty)"],
            "x ≥ 1 ⇒ x = 4": ["\\geq 1 \\Rightarrow x = 4"],
            "f′(x) = 9x²": ["f'(x)", "9x^{2}"],
            "arcsin(1/2) = π/6": ["\\arcsin", "\\frac{\\pi}{6}"],
            "√x dx": ["\\sqrt{x}"],
        }
        for line, needles in cases.items():
            tex = chain_to_mathtext(line)
            self.assertIsNotNone(tex, line)
            for needle in needles:
                self.assertIn(needle, tex, f"{line!r} -> {tex!r}")

    def test_cevrilemeyen_satir_none_doner(self):
        self.assertIsNone(chain_to_mathtext("x _ y?#"))
        self.assertIsNone(chain_to_mathtext(""))


if __name__ == "__main__":
    unittest.main()
