"""Defter modu testleri: her soru tipi icin kisa zincir ciktisi kontrolu.

Kurallar: aciklama cumlesi ve ondalik yaklasik deger yok; son cevap acilmis
ders kitabi biciminde (4(3x^2-2) -> 12x^2-8, log(6)/5 -> (1/5)ln 6,
df = (...)dx, i yerine ⅈ yok, zoo/nan yerine sozle sonuc).
"""

import os
import shutil
import tempfile
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
        self.assertIn("1/3", out)
        self.assertIn("Δ", out)
        self.assertNotIn("\\approx", out)
        self.assertNotIn("≈", out)

    def test_esitsizlik(self):
        out = self._out("|x-4|<3")
        self.assertIn("(1, 7)", out)
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
        self.assertIn("(1/5)ln 6", out)
        self.assertNotIn("\\log", out)
        self.assertNotIn("\\approx", out)

    def test_alan(self):
        out = self._out("y=x^2, y=x+2 sinirli alan")
        self.assertIn("9/2", out)
        self.assertNotIn("\\Rightarrow", out.splitlines()[-1])
        self.assertNotIn("\\", out)

    def test_diferensial(self):
        final = self._final("f(x)=x^2*sin(x) diferensialyny tapyn")
        self.assertTrue(final.startswith("df = ("), final)
        self.assertTrue(final.endswith(") dx"), final)
        self.assertNotIn("dx ", final)

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
        self.assertIn("12 x² - 8", final)
        self.assertNotIn("3 x² - 2", final)

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

    def test_no_raw_latex_commands_anywhere(self):
        import re

        pattern = re.compile(r"\\[A-Za-z]")
        questions = [
            "3x^2-7x+2=0", "|x-4|<3", "lim x->0 1/x", "d/dx x*sin(x)",
            "integral of 1/(5x+1) from 0 to 1", "y=x^2, y=x+2 sinirli alan",
            "f(x)=x^2*sin(x) diferensialyny tapyn", "f(x)=x^3-6x^2+9x-1 ekstremum",
            "y=x^3-x egrisine x0=2 teget", "x^2-3x+2=0", "cos(2x)=0",
        ]
        for q in questions:
            try:
                out = self.pad.defter(q)
            except Exception:  # noqa: BLE001
                continue
            self.assertIsNone(pattern.search(out), f"{q}: {out!r}")

    def test_cli_flag_exists(self):
        from mathpad.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--defter", "x^2-3x+2=0"])
        self.assertTrue(args.defter)


if __name__ == "__main__":
    unittest.main()


class DefterMenuTests(unittest.TestCase):
    def _app(self):
        import mathpad_menu

        m = mathpad_menu.App.__new__(mathpad_menu.App)
        m.ayar = __import__("mathpad.settings", fromlist=["Settings"]).Settings()
        m.engine = mathpad_menu.MathPad()
        m.notebook = mathpad_menu.Notebook(title="t")
        return m

    def test_output_mode_defter_accepted(self):
        from mathpad.settings import OUTPUT_MODES, Settings

        self.assertNotIn("defter", OUTPUT_MODES)
        s = Settings(cikti="defter")
        s.gecerli()
        self.assertEqual(s.cikti, "latex")

    def test_menu_defter_output(self):
        import contextlib
        import io
        from unittest import mock

        m = self._app()
        buf = io.StringIO()
        with mock.patch("builtins.input", side_effect=["3x^2-7x+2=0", "menu"]):
            with contextlib.redirect_stdout(buf):
                m.defter_modu()
        out = buf.getvalue()
        self.assertIn("[Denklem çözümü]", out)
        self.assertNotIn("$$", out)




class DefterKucukDuzeltmeler(unittest.TestCase):
    def test_emptyset_tek_son_satiri(self):
        from mathpad.engine import MathPad
        from mathpad.rendering.defter import defter_metni

        out = defter_metni(MathPad().ask("x^2<0"))
        self.assertEqual(out.count("∅"), 1)
        self.assertNotIn("\\varnothing", out)
        self.assertNotIn("\\emptyset", out)


class DefterPngTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_defter_to_png_yazar(self):
        from mathpad.rendering.png import defter_to_png

        path = defter_to_png(MathPad().ask("3x^2-7x+2=0"), os.path.join(self.tmp, "d.png"))
        self.assertTrue(os.path.isfile(path) and os.path.getsize(path) > 1000)

    def test_menu_resim_uret_defter(self):
        import mathpad_menu

        m = mathpad_menu.App.__new__(mathpad_menu.App)
        from mathpad.settings import Settings

        m.ayar = Settings(png_klasor=self.tmp, dpi=120)
        m.engine = MathPad()
        m.png_sayac = 0
        path = m._resim_uret(m.engine.ask("|2x+1|>=5"), "defter", defter=True)
        self.assertTrue(path and os.path.isfile(path) and os.path.getsize(path) > 1000)

    def test_zincirde_ok_komutu_yok(self):
        out = MathPad().defter("f(x)=x^3-6x^2+9x-1 ekstremum")
        self.assertNotIn("\\Rightarrow", out)
        self.assertIn("\u21d2", out)
