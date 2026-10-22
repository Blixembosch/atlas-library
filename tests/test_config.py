"""Tests for core/config.py."""

import unittest
from core.config import get_secret, safe_compare, CATEGORIES, APP_VERSION


class TestConfig(unittest.TestCase):
    def test_get_secret_default(self):
        val = get_secret("NON_EXISTING_SECRET_XYZ", default="test_val")
        self.assertEqual(val, "test_val")

    def test_safe_compare(self):
        self.assertTrue(safe_compare("atlas123", "atlas123"))
        self.assertFalse(safe_compare("atlas123", "wrong_password"))

    def test_constants(self):
        self.assertIn("Hikaye", CATEGORIES)
        self.assertIn("İlk Okuma", CATEGORIES)
        self.assertTrue(APP_VERSION.startswith("v"))


if __name__ == "__main__":
    unittest.main()
