import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vigenere_tool


class TestVigenere(unittest.TestCase):
    def test_known_vector(self):
        self.assertEqual(vigenere_tool.encode("ATTACKATDAWN", "LEMON"), "LXFOPVEFRNHR")

    def test_case_preserved(self):
        self.assertEqual(vigenere_tool.encode("AtTaCk", "lemon"), "LxFoPv")

    def test_non_letters_unchanged(self):
        self.assertEqual(vigenere_tool.encode("A A, 1!", "LEMON"), "L E, 1!")

    def test_decode_reverses(self):
        text = "Defend the east wall!"
        self.assertEqual(vigenere_tool.decode(vigenere_tool.encode(text, "GizliAnahtar"), "gizlianahtar"), text)

    def test_key_must_have_letters(self):
        with self.assertRaises(ValueError):
            vigenere_tool.encode("abc", "123")


if __name__ == "__main__":
    unittest.main()
