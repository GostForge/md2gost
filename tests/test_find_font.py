import sys
import unittest
from unittest.mock import patch

from md2gost.renderable import find_font as find_font_module


@unittest.skipUnless(sys.platform == "linux", "Strict font resolution test is Linux-specific")
class TestFindFontStrictLinux(unittest.TestCase):
    def setUp(self):
        find_font_module.find_font.cache_clear()

    def tearDown(self):
        find_font_module.find_font.cache_clear()

    def test_accepts_exact_family(self):
        with patch.object(
            find_font_module,
            "_resolve_fc_match",
            return_value=["/tmp/cour.ttf", "Courier New", "80", "0"],
        ):
            path = find_font_module.find_font("Courier New", False, False)

        self.assertEqual("/tmp/cour.ttf", path)

    def test_rejects_fallback_family(self):
        with patch.object(
            find_font_module,
            "_resolve_fc_match",
            return_value=["/tmp/libmono.ttf", "Liberation Mono", "80", "0"],
        ):
            with self.assertRaises(ValueError) as ctx:
                find_font_module.find_font("Courier New", False, False)

        self.assertIn("not installed exactly", str(ctx.exception))

    def test_rejects_missing_font(self):
        with patch.object(find_font_module, "_resolve_fc_match", return_value=None):
            with self.assertRaises(ValueError) as ctx:
                find_font_module.find_font("Courier New", False, False)

        self.assertIn("not available", str(ctx.exception))
