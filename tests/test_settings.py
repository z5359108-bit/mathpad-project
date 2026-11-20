import json
import os
import tempfile
import unittest

from mathpad.settings import Settings


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "ayarlar.json")

    def test_defaults(self):
        s = Settings()
        self.assertEqual(s.cikti, "latex")
        self.assertEqual(s.dpi, 160)
        self.assertTrue(s.latex_etkin)
        self.assertFalse(s.png_etkin)

    def test_save_and_load_roundtrip(self):
        s = Settings(cikti="png", dpi=220, png_klasor="res", defter_adi="not")
        s.save(self.path)
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["cikti"], "png")
        loaded = Settings.load(self.path)
        self.assertEqual(loaded, s)
        self.assertTrue(loaded.png_etkin)

    def test_load_missing_file_gives_defaults(self):
        self.assertEqual(Settings.load(self.path), Settings())

    def test_load_invalid_values_are_corrected(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"cikti": "bozuk", "dpi": 99999}, fh)
        s = Settings.load(self.path)
        self.assertEqual(s.cikti, "latex")
        self.assertEqual(s.dpi, 400)

    def test_load_broken_json_gives_defaults(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{geçersiz")
        self.assertEqual(Settings.load(self.path), Settings())


if __name__ == "__main__":
    unittest.main()
