"""Тесты для Md2GostConfig."""

import unittest
from docx.shared import Pt, Cm

from md2gost.config import Md2GostConfig, get_default_config, set_default_config
from md2gost import constants as C


class TestConfigDefaults(unittest.TestCase):
    """Все дефолты конфига === значениям из constants."""

    def test_default_font(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.font_main, C.FONT_MAIN)
        self.assertEqual(cfg.font_size_main, C.FONT_SIZE_MAIN)

    def test_default_margins(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.page_margin_left, C.PAGE_MARGIN_LEFT)
        self.assertEqual(cfg.page_margin_right, C.PAGE_MARGIN_RIGHT)
        self.assertEqual(cfg.page_margin_top, C.PAGE_MARGIN_TOP)
        self.assertEqual(cfg.page_margin_bottom, C.PAGE_MARGIN_BOTTOM)

    def test_default_caption_separator(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.caption_separator, C.CAPTION_SEPARATOR)

    def test_default_list_marker(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.list_marker, C.LIST_MARKER_UNORDERED)

    def test_default_syntax_highlighting_off(self):
        cfg = Md2GostConfig()
        self.assertFalse(cfg.syntax_highlighting)

    def test_default_debug_off(self):
        cfg = Md2GostConfig()
        self.assertFalse(cfg.debug)

    def test_default_sectional_numbering(self):
        cfg = Md2GostConfig()
        self.assertFalse(cfg.sectional_numbering)


class TestConfigOverride(unittest.TestCase):
    """Проверяем, что параметры можно переопределить."""

    def test_override_font(self):
        cfg = Md2GostConfig(font_main="Arial", font_size_main=Pt(12))
        self.assertEqual(cfg.font_main, "Arial")
        self.assertEqual(cfg.font_size_main, Pt(12))

    def test_override_margins(self):
        cfg = Md2GostConfig(page_margin_left=Cm(2.5))
        self.assertEqual(cfg.page_margin_left, Cm(2.5))
        # Остальные остались по умолчанию
        self.assertEqual(cfg.page_margin_right, C.PAGE_MARGIN_RIGHT)

    def test_override_marker(self):
        cfg = Md2GostConfig(list_marker="―")
        self.assertEqual(cfg.list_marker, "―")

    def test_override_separator(self):
        cfg = Md2GostConfig(caption_separator=" -- ")
        self.assertEqual(cfg.caption_separator, " -- ")

    def test_override_continuation(self):
        cfg = Md2GostConfig(
            table_continuation="Продолжение таблицы",
            listing_continuation="Продолжение листинга"
        )
        self.assertEqual(cfg.table_continuation, "Продолжение таблицы")


class TestGlobalConfig(unittest.TestCase):
    def setUp(self):
        set_default_config(None)

    def tearDown(self):
        set_default_config(None)

    def test_get_default_creates_instance(self):
        cfg = get_default_config()
        self.assertIsInstance(cfg, Md2GostConfig)

    def test_get_default_returns_same_instance(self):
        cfg1 = get_default_config()
        cfg2 = get_default_config()
        self.assertIs(cfg1, cfg2)

    def test_set_default(self):
        custom = Md2GostConfig(debug=True)
        set_default_config(custom)
        self.assertIs(get_default_config(), custom)
        self.assertTrue(get_default_config().debug)
