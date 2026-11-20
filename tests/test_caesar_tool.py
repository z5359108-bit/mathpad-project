import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import caesar_tool


class TestCaesar(unittest.TestCase):
    def test_encode_shift3(self):
        self.assertEqual(caesar_tool.encode("abc", 3), "def")

    def test_decode_shift3(self):
        self.assertEqual(caesar_tool.decode("def", 3), "abc")

    def test_wraparound(self):
        self.assertEqual(caesar_tool.encode("xyz", 3), "abc")

    def test_case_preserved(self):
        self.assertEqual(caesar_tool.encode("AbC", 3), "DeF")

    def test_non_letters_unchanged(self):
        self.assertEqual(caesar_tool.encode("a b, c!", 3), "d e, f!")

    def test_rot13_default(self):
        self.assertEqual(caesar_tool.encode("hello"), "uryyb")

    def test_double_encode_reverses(self):
        text = "HELLO world 123 !"
        self.assertEqual(caesar_tool.decode(caesar_tool.encode(text, 7), 7), text)


if __name__ == "__main__":
    unittest.main()
