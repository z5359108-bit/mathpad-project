"""Doğruluk paketi regresyon testleri: P0 sessiz-yanlış cevaplar, crash'ler,
geometri/sözel/fonksiyon değeri yetenekleri ve format/defter tutarlılığı."""

import unittest

import sympy as sp

from mathpad.engine import MathPad
from mathpad.rendering.defter import defter_metni


class Harness(unittest.TestCase):
    def setUp(self):
        self.mp = MathPad()

    def check(self, question, expected, solver=None):
        solution = self.mp.ask(question)
        self.assertEqual(solution.result, expected)
        if solver is not None:
            self.assertEqual(solution.solver, solver)

    def check_raises(self, question, fragment):
        with self.assertRaises(Exception) as ctx:
            self.mp.ask(question)
        self.assertIn(fragment.lower(), str(ctx.exception).lower())


class TestFaktoriyel(Harness):
    def test_oran(self):
        self.check("7!/5!", 42, solver="arithmetic")

    def test_bilesik(self):
        self.check("5!/10", 12, solver="arithmetic")

    def test_toplam(self):
        self.check("3!+2!", 8, solver="arithmetic")

    def test_yalniz(self):
        self.check("120!", sp.factorial(120), solver="arithmetic")


class TestDenklemKenarDurumlari(Harness):
    def test_cozum_yok(self):
        s = self.mp.ask("x + 1 = x + 2")
        self.assertEqual(s.solver, "algebra")

    def test_ozdeslik(self):
        s = self.mp.ask("4x + 2 = 4x + 2")
        self.assertEqual(s.solver, "algebra")
        self.assertIn("özdeşlik", s.result_text)


class TestYonlendirme(Harness):
    def test_sum_calculus(self):
        self.check("sum n from 1 to 100", 5050, solver="calculus")

    def test_sum_esit(self):
        self.check("sum k=1 to 10 of k^2", 385, solver="calculus")

    def test_ters_matris(self):
        s = self.mp.ask("ters [[2,0],[0,1]]")
        self.assertEqual(s.solver, "linear_algebra")
        self.assertEqual(str(s.result), "Matrix([[1/2, 0], [0, 1]])")

    def test_det_kare_olmayan(self):
        self.check_raises("det [[1,2,3],[4,5,6]]", "kare matris")

    def test_bolme_sifira(self):
        self.check_raises("x/0", "tanımsız")

    def test_varyans_populasyon(self):
        self.check("varyans 2 4 6 8", 5, solver="statistics")

    def test_varians_yazim(self):
        self.check("varians 2 4 6 8", 5, solver="statistics")

    def test_standart_sapma_populasyon(self):
        s = self.mp.ask("standart sapma 2 4 6 8")
        self.assertEqual(s.solver, "statistics")
        self.assertAlmostEqual(float(s.result), float(sp.sqrt(5)), places=9)


class TestTepeDonumNoktasi(Harness):
    def test_donum(self):
        s = self.mp.ask("donum noktasi x^2-6x+5")
        self.assertEqual(s.result, (3, -4))

    def test_tepe(self):
        s = self.mp.ask("tepe noktasi x^2-6x+5")
        self.assertEqual(s.result, (3, -4))

    def test_parabol_tepesi(self):
        s = self.mp.ask("parabolin tepesi x^2+4x+1")
        self.assertEqual(s.result, (-2, -3))

    def test_kubuk_bukulma(self):
        self.check("donum noktasi x^3-3x", [(0, 0)])


class TestKalkulusFormatlari(Harness):
    def test_belirsiz(self):
        s = self.mp.ask("integral x^2 dx")
        self.assertEqual(str(s.result), "x**3/3")

    def test_belirsiz_int_kisa(self):
        s = self.mp.ask("int x^2 dx")
        self.assertEqual(str(s.result), "x**3/3")

    def test_unicode_belim(self):
        s = self.mp.ask("∫_0^1 x^2 dx")
        self.assertEqual(s.result, sp.Rational(1, 3))

    def test_belirli_belgen_Ingilizce(self):
        s = self.mp.ask("integral x^2 from 0 to 2")
        self.assertEqual(s.result, sp.Rational(8, 3))

    def test_taylor_at(self):
        s = self.mp.ask("taylor sin(x) at 0")
        self.assertEqual(s.solver, "calculus")

    def test_taylor_civarinda(self):
        s = self.mp.ask("taylor e^x civarında 0")

    def test_turev(self):
        s = self.mp.ask("turev x^3")
        self.assertEqual(str(s.result), "3*x**2")


class TestGeometri(Harness):
    def test_hipotenus_yaln_numaralar(self):
        self.check("3 4 5 hipotenus", 5, solver="geometry")

    def test_hipotenus_etiketli(self):
        self.check("dik ucgen dik kenarlari 3 ve 4 hipotenus", 5, solver="geometry")

    def test_daire_alan(self):
        s = self.mp.ask("dairenin alani r=3")
        self.assertEqual(s.result, sp.pi * 9)

    def test_daire_cevre(self):
        s = self.mp.ask("dairenin cevresi r=3")
        self.assertEqual(s.result, sp.pi * 6)

    def test_cember_cevre(self):
        s = self.mp.ask("cemberin cevresi r=5")
        self.assertEqual(s.result, sp.pi * 10)

    def test_kare_alan(self):
        self.check("karenin alani kenar 5", 25, solver="geometry")

    def test_kare_cevre(self):
        self.check("karenin cevresi kenar 7", 28, solver="geometry")

    def test_dikdortgen_alan(self):
        self.check("dikdortgenin alani kenarlari 3 ve 4", 12, solver="geometry")

    def test_ucgen_alan(self):
        self.check("ucgenin alani taban 6 yukseklik 4", 12, solver="geometry")

    def test_kure_hacim(self):
        s = self.mp.ask("kurenin hacmi r=2")
        self.assertEqual(s.result, sp.Rational(32, 3) * sp.pi)

    def test_silindir_hacim(self):
        s = self.mp.ask("silindirin hacmi r=2 h=5")
        self.assertEqual(s.result, sp.pi * 20)

    def test_kup_hacim(self):
        self.check("kupun hacmi kenar 3", 27, solver="geometry")

    def test_dik_ucgen_fallback(self):
        self.check("3 4 5 dik ucgen", 5, solver="geometry")

    def test_polinom_bolme(self):
        s = self.mp.ask("polinom bolme (x^3-1)/(x-1)")
        self.assertEqual(s.solver, "algebra")
        self.assertEqual(str(s.result), "x**2 + x + 1")

    def test_polinom_bolme_kalan(self):
        s = self.mp.ask("polinom bolme (x^3-2x+4)/(x-2)")
        self.assertIn("kalan", str(s.result_tex))

    def test_kure_not_routing(self):
        gs = next(s for s in self.mp.solvers if s.name == "geometry")
        for q in ("f(x) sinus", "integral x", "turev x^2", "matris [1,2]"):
            self.assertEqual(gs.can_handle(q), 0.0)


class TestSozelVeFonksiyonDegeri(Harness):
    def test_kat_fazla(self):
        self.check("Bir sayinin 3 katinin 5 fazlasi 20 ise sayi kactir", 5, solver="word_problems")

    def test_kat_fazla_eksik(self):
        self.check("bir sayinin 4 katinin 3 eksigi 17", 5, solver="word_problems")

    def test_kat(self):
        self.check("sayinin 3 kati 24 ise", 8, solver="word_problems")

    def test_yarisi(self):
        self.check("sayinin yarisi 42", 84, solver="word_problems")

    def test_iki_sayi(self):
        s = self.mp.ask("iki sayinin toplami 15 farki 3")
        self.assertEqual(list(s.result), [9, 6])

    def test_func_deger_atama(self):
        self.check("f(x)=3x+2 fonksiyonunun x=2 deki degeri", 8, solver="word_problems")

    def test_func_deger_f(self):
        self.check("f(x)=3x+2 fonksiyonunun degelik f(2)", 8, solver="word_problems")

    def test_func_ne_routing(self):
        ws = next(s for s in self.mp.solvers if s.name == "word_problems")
        for q in ("f(g(x)) turevi", "x^2-6x+5", "matris [1,2]"):
            self.assertEqual(ws.can_handle(q), 0.0)


class TestDefterModu(Harness):
    def test_faktoriyel_defter_cdots(self):
        metin = defter_metni(self.mp.ask("7!/5!"))
        self.assertNotIn("·s", metin)
        self.assertIn("42", metin)

    def test_geometri_defter(self):
        metin = defter_metni(self.mp.ask("dairenin alani r=3"))
        self.assertIn("π", metin)

    def test_sozel_defter(self):
        metin = defter_metni(self.mp.ask("sayinin 3 kati 24 ise"))
        self.assertIn("8", metin)

    def test_png_modu_cikar(self):
        import tempfile, os
        import sympy as sp
        from mathpad.rendering.png import solution_to_png
        s = self.mp.ask("tepe noktasi x^2-6x+5")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tepe.png")
            out = solution_to_png(s, path)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(os.path.getsize(out), 1000)

    def test_png_geometri(self):
        import tempfile, os
        from mathpad.rendering.png import solution_to_png
        s = self.mp.ask("kurenin hacmi r=2")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "kure.png")
            out = solution_to_png(s, path)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(os.path.getsize(out), 1000)


class TestProgramatikKullanim(Harness):
    def test_ask_many(self):
        sols = self.mp.ask_many("2+2", "7!/5!", "sum n from 1 to 100")
        self.assertEqual([str(x.result) for x in sols], ["4", "42", "5050"])

    def test_yeterli_solver(self):
        self.assertTrue(len(self.mp.solvers) >= 11)

    def test_bare_sayi(self):
        self.check("85", 85, solver="arithmetic")


if __name__ == "__main__":
    unittest.main()
