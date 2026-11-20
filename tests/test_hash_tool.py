import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hash_tool


class TestHash(unittest.TestCase):
    def test_sha256_known_vector(self):
        self.assertEqual(
            hash_tool.digest(b"hello", "sha256"),
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        )

    def test_md5_known_vector(self):
        self.assertEqual(
            hash_tool.digest(b"hello", "md5"),
            "5d41402abc4b2a76b9719d911017c592",
        )

    def test_empty_input(self):
        self.assertEqual(
            hash_tool.digest(b"", "sha256"),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_deterministic(self):
        self.assertEqual(hash_tool.digest(b"a", "sha512"), hash_tool.digest(b"a", "sha512"))

    def test_unsupported_algorithm(self):
        with self.assertRaises(ValueError):
            hash_tool.digest(b"a", "sha999")


if __name__ == "__main__":
    unittest.main()
