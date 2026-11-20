import base64
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64_tool as b64


class TestEncode(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(b64.encode("hello"), base64.b64encode(b"hello").decode())

    def test_utf8(self):
        self.assertEqual(b64.encode("Selam Dünya"), "U2VsYW0gRMO8bnlh")

    def test_empty(self):
        self.assertEqual(b64.encode(""), "")


class TestDecode(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(b64.decode("aGVsbG8="), "hello")

    def test_utf8(self):
        self.assertEqual(b64.decode("U2VsYW0gRMO8bnlh"), "Selam Dünya")

    def test_roundtrip(self):
        text = "Zeyrox 123! ÇĞİÖŞÜ — çğışöü"
        self.assertEqual(b64.decode(b64.encode(text)), text)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            b64.decode("!!!geçersiz!!!")


if __name__ == "__main__":
    unittest.main()
