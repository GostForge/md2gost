"""Тесты для Md2GostConfig."""

import tempfile
import unittest
from pathlib import Path
from docx.shared import Cm, Mm, Pt

from md2gost.config import (
    CaptionTextStyle,
    Md2GostConfig,
    get_default_config,
    get_config_reference,
    load_config_from_yaml,
    load_project_config,
    set_default_config,
)


class TestConfigDefaults(unittest.TestCase):
    """Проверяем ключевые дефолты конфигурации."""

    def test_default_font(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.font_main, "Times New Roman")
        self.assertEqual(cfg.font_size_main, Pt(14))

    def test_default_margins(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.page_width_a4, Mm(210))
        self.assertEqual(cfg.page_height_a4, Mm(297))
        self.assertEqual(cfg.page_margin_left, Cm(3.0))
        self.assertEqual(cfg.page_margin_right, Cm(1.0))
        self.assertEqual(cfg.page_margin_top, Cm(2.0))
        self.assertEqual(cfg.page_margin_bottom, Cm(2.0))

    def test_default_caption_separator(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.caption_separator, " \u2014 ")

    def test_default_list_marker(self):
        cfg = Md2GostConfig()
        self.assertEqual(cfg.list_marker, "●")

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
        self.assertEqual(cfg.page_margin_right, Cm(1.0))

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


class TestYamlConfig(unittest.TestCase):
    def test_load_empty_yaml(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "gostforge.yml"
            path.write_text("", encoding="utf-8")

            cfg = load_config_from_yaml(path)
            self.assertIsInstance(cfg, Md2GostConfig)
            self.assertEqual(cfg.title_pages, 1)

    def test_load_nested_md2gost_generator_section(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "gostforge.yml"
            path.write_text(
                """
md2gost:
  generator:
    title-pages: 2
    syntax-highlighting: true
    caption_separator: " :: "
    font_size_main: 13pt
    page_margin_left: 2.5cm
    caption_image_style: bold|underline
""".strip(),
                encoding="utf-8",
            )

            cfg = load_config_from_yaml(path)
            self.assertEqual(cfg.title_pages, 2)
            self.assertTrue(cfg.syntax_highlighting)
            self.assertEqual(cfg.caption_separator, " :: ")
            self.assertEqual(cfg.font_size_main, Pt(13))
            self.assertEqual(cfg.page_margin_left, Cm(2.5))
            self.assertEqual(
                cfg.caption_image_style,
                CaptionTextStyle.BOLD | CaptionTextStyle.UNDERLINE,
            )

    def test_load_unknown_field_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "gostforge.yml"
            path.write_text(
                """
md2gost:
  unknown_option: 1
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_config_from_yaml(path)

    def test_load_invalid_length_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "gostforge.yml"
            path.write_text(
                """
md2gost:
  page_margin_left: abc
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_config_from_yaml(path)

    def test_load_missing_project_config_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing_gostforge.yml"
            cfg = load_project_config(missing_path, allow_missing=True)
            self.assertIsInstance(cfg, Md2GostConfig)

    def test_load_missing_project_config_raises_when_not_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing_gostforge.yml"
            with self.assertRaises(FileNotFoundError):
                load_project_config(missing_path, allow_missing=False)


class TestConfigReference(unittest.TestCase):
    def test_reference_contains_page_size_defaults(self):
        reference = get_config_reference()
        self.assertIn("page_width_a4", reference)
        self.assertIn("page_height_a4", reference)
        self.assertEqual(reference["page_width_a4"]["default"]["twips"], int(Mm(210).twips))

    def test_reference_contains_field_docs(self):
        reference = get_config_reference()
        self.assertIn("doc", reference["page_width_a4"])
        self.assertTrue(reference["page_width_a4"]["doc"])
