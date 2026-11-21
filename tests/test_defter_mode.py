"""Defter modu testleri: her soru tipi icin kisa zincir ciktisi kontrolu.

Kurallar: aciklama cumlesi ve ondalik yaklasik deger yok; son cevap acilmis
ders kitabi biciminde (4(3x^2-2) -> 12x^2-8, log(6)/5 -> (1/5)ln 6,
df = (...)dx, i yerine ⅈ yok, zoo/nan yerine sozle sonuc).
"""

import unittest

from mathpad import MathPad


class DefterModeTests(unittest.TestCase):
    def setUp(self):
        self.pad = MathPad()

    def _out(self, question: str) -> str:
        return self.pad.defter(question)

    def _final(self, question: str) -> str:
        lines = [line for line in self._out(question).splitlines() if line.strip()]
        return lines[-1]

    # ------------------------------------------------------------- soru tipleri
    def test_denklem(self):
        out = self._out("3x^2-7x+2=0")
        self.assertIn("\\frac{1}{3}", out)
        self.assertIn("\\Delta", out)
        self.assertNotIn("\\approx", out)
        self.assertNotIn("≈", out)

    def test_esitsizlik(self):
        out = self._out("|x-4|<3")
        self.assertIn("\\left(1, 7\\right)", out)
        self.assertNotIn("\\approx", out)

    def test_limit(self):
        out = self._out("lim x->0 1/x")
        self.assertIn("mevcut değil", out)
        self.assertNotIn("zoo", out)
        self.assertNotIn("nan", out)

    def test_turev(self):
        out = self._out("d/dx x*sin(x)")
        self.assertIn("cos", out)
        self.assertIn("sin", out)

    def test_integral(self):
        out = self._out("integral of 1/(5x+1) from 0 to 1")
        self.assertIn("\\frac{1}{5}\\ln 6", out)
        self.assertNotIn("\\log", out)
        self.assertNotIn("\\approx", out)

    def test_alan(self):
        out = self._out("y=x^2, y=x+2 sinirli alan")
        self.assertIn("\\frac{9}{2}", out)
        self.assertNotIn("\\Rightarrow", out.splitlines()[-1])

    def test_diferensial(self):
        final = self._final("f(x)=x^2*sin(x) diferensialyny tapyn")
        self.assertTrue(final.startswith("df = "))
        self.assertTrue(final.endswith("\\,dx"))
        self.assertNotIn("dx ", final[len("df = "):-len("\\,dx")])

    def test_ekstremum(self):
        final = self._final("f(x)=x^3-6x^2+9x-1 ekstremum")
        self.assertIn("⇒", final)
        self.assertNotIn("\\Rightarrow", final)
        self.assertIn("f = 3", final)
        self.assertIn("f = -1", final)

    def test_teget(self):
        final = self._final("y=x^3-x eğrisine x0=2 teğet")
        self.assertIn("11 x - 16", final)

    # --------------------------------------------------- biçim kuralları
    def test_polynomial_answer_expanded(self):
        final = self._final("f(x)=x^4-4x^2 ikinji önüm")
        self.assertIn("12 x^{2} - 8", final)
        self.assertNotIn("3 x^{2} - 2", final)

    def test_factor_request_keeps_factored(self):
        out = self._out("x^4-16 çarpanlarına ayır")
        self.assertIn("x + 2", out)

    def test_no_imaginary_unicode(self):
        out = self._out("(3+i)/(1-i)")
        self.assertNotIn("ⅈ", out)
        self.assertIn("i", out)

    def test_no_explanation_sentences(self):
        out = self._out("y=sin(x), y=0, x=0, x=pi meydany")
        for line in out.splitlines():
            self.assertFalse(line.endswith("."), line)

    def test_chain_has_no_approx_lines(self):
        out = self._out("log_2(x)=x-3")
        self.assertNotIn("\\approx", out)
        self.assertNotIn("≈", out)

    def test_cli_flag_exists(self):
        from mathpad.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--defter", "x^2-3x+2=0"])
        self.assertTrue(args.defter)


if __name__ == "__main__":
    unittest.main()


class DefterMenuTests(unittest.TestCase):
    def test_output_mode_defter_accepted(self):
        from mathpad.settings import OUTPUT_MODES, Settings

        self.assertIn("defter", OUTPUT_MODES)
        s = Settings(cikti="defter")
        s.gecerli()
        self.assertEqual(s.cikti, "defter")
        self.assertTrue(s.defter_etkin)
        self.assertFalse(s.latex_etkin)

    def test_menu_defter_output(self):
        import io
        import contextlib
        import mathpad_menu

        m = mathpad_menu.App.__new__(mathpad_menu.App)
        m.ayar = __import__("mathpad.settings", fromlist=["Settings"]).Settings(cikti="defter")
        m.engine = mathpad_menu.MathPad()
        sol = m.engine.ask("3x^2-7x+2=0")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m._cozum_goster(sol)
        out = buf.getvalue()
        self.assertIn("[Denklem çözümü]", out)
        self.assertNotIn("$$", out)
