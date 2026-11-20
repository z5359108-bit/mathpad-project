import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xor_tool


class TestXor(unittest.TestCase):
    def test_encode_empty(self):
        self.assertEqual(xor_tool.encode("", "key"), "")

    def test_known_vector(self):
        encoded = xor_tool.encode("A", "K")
        self.assertEqual(int(encoded, 16), ord("A") ^ ord("K"))

    def test_decode_reverses(self):
        text = "Gizli mesaj ÇĞİÖŞÜ 123!"
        self.assertEqual(xor_tool.decode(xor_tool.encode(text, "anahtar"), "anahtar"), text)

    def test_decode_invalid_hex(self):
        with self.assertRaises(ValueError):
            xor_tool.decode("!!!geçersiz!!", "key")

    def test_empty_key_rejected(self):
        with self.assertRaises(ValueError):
            xor_tool.encode("abc", "")


if __name__ == "__main__":
    unittest.main()
