"""Тесты дефолтных значений Md2GostConfig."""

import unittest
from docx.shared import Pt, Cm, Mm, Twips

from md2gost.config import Md2GostConfig


def _cfg() -> Md2GostConfig:
    return Md2GostConfig()


class TestPageConstants(unittest.TestCase):
    """Проверяем, что поля страницы соответствуют ГОСТ."""

    def test_page_margins_gost(self):
        cfg = _cfg()
        self.assertEqual(cfg.page_margin_left, Cm(3.0))
        self.assertEqual(cfg.page_margin_right, Cm(1.0))
        self.assertEqual(cfg.page_margin_top, Cm(2.0))
        self.assertEqual(cfg.page_margin_bottom, Cm(2.0))

    def test_page_size_a4(self):
        cfg = _cfg()
        self.assertEqual(cfg.page_width_a4, Mm(210))
        self.assertEqual(cfg.page_height_a4, Mm(297))


class TestFontConstants(unittest.TestCase):
    def test_main_font(self):
        cfg = _cfg()
        self.assertEqual(cfg.font_main, "Times New Roman")
        self.assertEqual(cfg.font_size_main, Pt(14))

    def test_code_font(self):
        cfg = _cfg()
        self.assertEqual(cfg.font_code, "Courier New")
        self.assertEqual(cfg.font_size_code, Pt(10))

    def test_line_spacing(self):
        self.assertEqual(_cfg().line_spacing, 1.5)

    def test_first_line_indent(self):
        self.assertEqual(_cfg().first_line_indent, Cm(1.25))


class TestHeadingConstants(unittest.TestCase):
    def test_heading1_size(self):
        self.assertEqual(_cfg().heading1_font_size, Pt(18))

    def test_heading2_size(self):
        self.assertEqual(_cfg().heading2_font_size, Pt(16))

    def test_heading3_size(self):
        self.assertEqual(_cfg().heading3_font_size, Pt(14))

    def test_heading_spacing(self):
        cfg = _cfg()
        self.assertEqual(cfg.heading2_space_before, Pt(24))
        self.assertEqual(cfg.heading3_space_before, Pt(24))
        self.assertEqual(cfg.heading1_space_after, Pt(12))


class TestCaptionConstants(unittest.TestCase):
    def test_separator_is_em_dash(self):
        self.assertIn("\u2014", _cfg().caption_separator)

    def test_categories_russian(self):
        cfg = _cfg()
        self.assertEqual(cfg.caption_table, "Таблица")
        self.assertEqual(cfg.caption_image, "Рисунок")
        self.assertEqual(cfg.caption_listing, "Листинг")
        self.assertEqual(cfg.caption_equation, "Формула")

    def test_continuation_capitalization(self):
        """ГОСТ: 'Продолжение Таблицы' с большой буквы."""
        cfg = _cfg()
        self.assertTrue(cfg.table_continuation.startswith("Продолжение Т"))
        self.assertTrue(cfg.listing_continuation.startswith("Продолжение Л"))


class TestListConstants(unittest.TestCase):
    def test_marker(self):
        self.assertIn(_cfg().list_marker, ["●", "■", "○", "―", "--"])

    def test_indent_positive(self):
        cfg = _cfg()
        self.assertGreater(cfg.list_marker_indent, 0)
        self.assertGreater(cfg.list_level_indent, 0)


class TestStyleNames(unittest.TestCase):
    def test_style_names_non_empty(self):
        cfg = _cfg()
        for name in [
            cfg.style_normal,
            cfg.style_caption,
            cfg.style_code,
            cfg.style_table_grid,
            cfg.style_normal_table,
            cfg.style_formula_content,
            cfg.style_formula_numbering,
        ]:
            self.assertTrue(len(name) > 0, f"Empty style name: {name}")
