import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import password_gen_tool


class TestPasswordGen(unittest.TestCase):
    def test_default_pool(self):
        pw = password_gen_tool.generate(50)
        self.assertEqual(len(pw), 50)
        self.assertTrue(any(c.islower() for c in pw))
        self.assertTrue(any(c.isupper() for c in pw))
        self.assertTrue(any(c.isdigit() for c in pw))
        self.assertTrue(any(not c.isalnum() for c in pw))

    def test_length(self):
        self.assertEqual(len(password_gen_tool.generate(5)), 5)

    def test_no_symbols(self):
        pw = password_gen_tool.generate(50, symbols=False)
        self.assertTrue(all(c.isalnum() for c in pw))

    def test_only_digits(self):
        pw = password_gen_tool.generate(20, lower=False, upper=False, symbols=False)
        self.assertTrue(all(c.isdigit() for c in pw))

    def test_uniqueness(self):
        sample = {password_gen_tool.generate(32) for _ in range(20)}
        self.assertEqual(len(sample), 20)

    def test_empty_pool_rejected(self):
        with self.assertRaises(ValueError):
            password_gen_tool.generate(10, lower=False, upper=False, digits=False, symbols=False)

    def test_zero_length_rejected(self):
        with self.assertRaises(ValueError):
            password_gen_tool.generate(0)


if __name__ == "__main__":
    unittest.main()
