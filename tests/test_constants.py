"""Тесты для md2gost.constants — проверяем, что значения в здравых пределах."""

import unittest
from docx.shared import Pt, Cm, Mm, Twips

from md2gost import constants as C


class TestPageConstants(unittest.TestCase):
    """Проверяем, что поля страницы соответствуют ГОСТ."""

    def test_page_margins_gost(self):
        self.assertEqual(C.PAGE_MARGIN_LEFT, Cm(3.0))
        self.assertEqual(C.PAGE_MARGIN_RIGHT, Cm(1.0))
        self.assertEqual(C.PAGE_MARGIN_TOP, Cm(2.0))
        self.assertEqual(C.PAGE_MARGIN_BOTTOM, Cm(2.0))

    def test_page_size_a4(self):
        self.assertEqual(C.PAGE_WIDTH_A4, Mm(210))
        self.assertEqual(C.PAGE_HEIGHT_A4, Mm(297))


class TestFontConstants(unittest.TestCase):
    def test_main_font(self):
        self.assertEqual(C.FONT_MAIN, "Times New Roman")
        self.assertEqual(C.FONT_SIZE_MAIN, Pt(14))

    def test_code_font(self):
        self.assertEqual(C.FONT_CODE, "Courier New")
        self.assertEqual(C.FONT_SIZE_CODE, Pt(10))

    def test_line_spacing(self):
        self.assertEqual(C.LINE_SPACING_MAIN, 1.5)

    def test_first_line_indent(self):
        self.assertEqual(C.FIRST_LINE_INDENT, Cm(1.25))


class TestHeadingConstants(unittest.TestCase):
    def test_heading1_size(self):
        self.assertEqual(C.HEADING1_FONT_SIZE, Pt(18))

    def test_heading2_size(self):
        self.assertEqual(C.HEADING2_FONT_SIZE, Pt(16))

    def test_heading3_size(self):
        self.assertEqual(C.HEADING3_FONT_SIZE, Pt(14))

    def test_heading_spacing(self):
        self.assertEqual(C.HEADING2_SPACE_BEFORE, Pt(24))
        self.assertEqual(C.HEADING3_SPACE_BEFORE, Pt(24))
        self.assertEqual(C.HEADING1_SPACE_AFTER, Pt(12))


class TestCaptionConstants(unittest.TestCase):
    def test_separator_is_em_dash(self):
        self.assertIn("\u2014", C.CAPTION_SEPARATOR)

    def test_categories_russian(self):
        self.assertEqual(C.TABLE_CAPTION_CATEGORY, "Таблица")
        self.assertEqual(C.IMAGE_CAPTION_CATEGORY, "Рисунок")
        self.assertEqual(C.LISTING_CAPTION_CATEGORY, "Листинг")
        self.assertEqual(C.EQUATION_CAPTION_CATEGORY, "Формула")

    def test_continuation_capitalization(self):
        """ГОСТ: 'Продолжение Таблицы' с большой буквы."""
        self.assertTrue(C.TABLE_CONTINUATION_PREFIX.startswith("Продолжение Т"))
        self.assertTrue(C.LISTING_CONTINUATION_PREFIX.startswith("Продолжение Л"))


class TestListConstants(unittest.TestCase):
    def test_marker(self):
        self.assertIn(C.LIST_MARKER_UNORDERED, ["●", "■", "○", "―", "--"])

    def test_indent_positive(self):
        self.assertGreater(C.LIST_MARKER_INDENT, 0)
        self.assertGreater(C.LIST_LEVEL_INDENT, 0)


class TestStyleNames(unittest.TestCase):
    def test_style_names_non_empty(self):
        for name in [C.STYLE_NORMAL, C.STYLE_CAPTION, C.STYLE_CODE,
                     C.STYLE_TABLE_GRID, C.STYLE_NORMAL_TABLE,
                     C.STYLE_FORMULA_CONTENT, C.STYLE_FORMULA_NUMBERING]:
            self.assertTrue(len(name) > 0, f"Empty style name: {name}")
