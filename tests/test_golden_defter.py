"""Altın defter testleri: golden_defter.json'daki her sorunun defter
çıktısı beklenen zincirle karşılaştırılır (boşluk farkları yok sayılır)."""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mathpad import MathPad

GOLDEN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "golden_defter.json")


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


class TestGoldenDefter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GOLDEN_PATH, encoding="utf-8") as f:
            cls.golden = json.load(f)["sorular"]
        cls.pad = MathPad()

    def test_count(self):
        self.assertGreaterEqual(len(self.golden), 42)

    def test_all_defter_lines(self):
        hatalar = []
        for item in self.golden:
            beklenen = [_norm(l) for l in item["defter"]]
            try:
                gelen = [_norm(l) for l in self.pad.defter(item["soru"]).splitlines()]
            except Exception as exc:  # noqa: BLE001
                gelen = [f"<HATA: {type(exc).__name__}>"]
            if gelen != beklenen:
                hatalar.append((item["soru"], beklenen, gelen))
        if hatalar:
            mesaj = "\n\n".join(
                f"SORU: {s}\nBEKLENEN: {b}\nGİREN: {g}" for s, b, g in hatalar)
            self.fail(f"{len(hatalar)} altın defter sorusu farklı çıktı:\n{mesaj}")


if __name__ == "__main__":
    unittest.main()
