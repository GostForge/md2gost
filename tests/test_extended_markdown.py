"""Тесты парсинга Extended Markdown — заголовки, формулы, TOC, caption, ссылки, таблицы."""

import unittest

from md2gost.extended_markdown import (
    markdown, Heading, SetextHeading, Equation, TOC, Caption,
    Table, Paragraph, FencedCode,
)
from md2gost.extended_markdown.reference import Reference
from md2gost.extended_markdown.inline_formula import InlineEquation
from md2gost.extended_markdown.image import Image


class TestHeadingParsing(unittest.TestCase):
    def test_numbered_heading(self):
        result = markdown.parse("# Заголовок\n").children[0]
        self.assertIsInstance(result, Heading)
        self.assertEqual(result.level, 1)
        self.assertTrue(result.numbered)

    def test_unnumbered_heading(self):
        result = markdown.parse("# *Введение\n").children[0]
        self.assertIsInstance(result, Heading)
        self.assertEqual(result.level, 1)
        self.assertFalse(result.numbered)

    def test_heading_levels(self):
        for level in range(1, 7):
            hashes = "#" * level
            result = markdown.parse(f"{hashes} Test\n").children[0]
            self.assertIsInstance(result, Heading)
            self.assertEqual(result.level, level)

    def test_heading_content(self):
        result = markdown.parse("## Мой подраздел\n").children[0]
        # marko parses inline content into children; inline_body is consumed
        from marko.inline import RawText
        self.assertEqual(len(result.children), 1)
        self.assertIsInstance(result.children[0], RawText)
        self.assertEqual(result.children[0].children, "Мой подраздел")


class TestEquationParsing(unittest.TestCase):
    def test_single_line_equation(self):
        result = markdown.parse("$$ E = mc^2 $$\n").children[0]
        self.assertIsInstance(result, Equation)
        self.assertEqual(result.latex_equation, "E = mc^2")

    def test_multiline_equation(self):
        result = markdown.parse("$$\nx^2 + y^2 = z^2\n$$\n").children[0]
        self.assertIsInstance(result, Equation)
        self.assertEqual(result.latex_equation, "x^2 + y^2 = z^2")

    def test_equation_with_sum(self):
        result = markdown.parse("$$\n\\sum_{i=1}^{n} i\n$$\n").children[0]
        self.assertIsInstance(result, Equation)
        self.assertIn("\\sum", result.latex_equation)


class TestTOCParsing(unittest.TestCase):
    def test_toc(self):
        result = markdown.parse("[TOC]\n").children[0]
        self.assertIsInstance(result, TOC)


class TestCaptionParsing(unittest.TestCase):
    def test_caption_with_text(self):
        result = markdown.parse("%goods Продукты\n").children[0]
        self.assertIsInstance(result, Caption)
        self.assertEqual(result.unique_name, "goods")
        self.assertEqual(result.text, "Продукты")

    def test_caption_without_text(self):
        result = markdown.parse("%myref\n").children[0]
        self.assertIsInstance(result, Caption)
        self.assertEqual(result.unique_name, "myref")
        self.assertIsNone(result.text)


class TestTableParsing(unittest.TestCase):
    def test_simple_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        result = markdown.parse(md).children[0]
        self.assertIsInstance(result, Table)
        self.assertEqual(len(result.children), 2)  # header row + data row
        self.assertEqual(len(result.children[0].children), 2)  # 2 columns

    def test_table_alignment(self):
        md = "| L | C | R |\n|:--|:--:|--:|\n| a | b | c |\n"
        result = markdown.parse(md).children[0]
        self.assertIsInstance(result, Table)
        cells = result.children[1].children
        self.assertEqual(cells[0].align, "left")
        self.assertEqual(cells[1].align, "center")
        self.assertEqual(cells[2].align, "right")


class TestInlineElements(unittest.TestCase):
    def test_inline_formula(self):
        result = markdown.parse("Формула $x^2$ в тексте\n").children[0]
        self.assertIsInstance(result, Paragraph)
        has_formula = any(isinstance(c, InlineEquation) for c in result.children)
        self.assertTrue(has_formula, "InlineEquation not found in paragraph children")

    def test_reference(self):
        result = markdown.parse("Ссылка на @myref в тексте\n").children[0]
        self.assertIsInstance(result, Paragraph)
        has_ref = any(isinstance(c, Reference) for c in result.children)
        self.assertTrue(has_ref, "Reference not found in paragraph children")

    def test_image_with_caption(self):
        result = markdown.parse("![](img.png \"Подпись\")\n").children[0]
        self.assertIsInstance(result, Paragraph)
        img = None
        for c in result.children:
            if isinstance(c, Image):
                img = c
                break
        self.assertIsNotNone(img)
        self.assertEqual(img.title, "Подпись")

    def test_image_with_unique_name(self):
        result = markdown.parse("![](img.png \"%myimg Подпись\")\n").children[0]
        img = [c for c in result.children if isinstance(c, Image)][0]
        self.assertEqual(img.unique_name, "myimg")


class TestFencedCodeParsing(unittest.TestCase):
    def test_code_block(self):
        md = "```python\nprint('hello')\n```\n"
        result = markdown.parse(md).children[0]
        self.assertIsInstance(result, FencedCode)
        self.assertEqual(result.lang, "python")
        self.assertIn("print", result.children[0].children)

    def test_code_block_with_filename(self):
        md = "```python myfile.py\ncode\n```\n"
        result = markdown.parse(md).children[0]
        self.assertIsInstance(result, FencedCode)
        self.assertEqual(result.extra, "myfile.py")


class TestParagraphParsing(unittest.TestCase):
    def test_plain_paragraph(self):
        result = markdown.parse("Простой абзац текста.\n").children[0]
        self.assertIsInstance(result, Paragraph)

    def test_bold_italic(self):
        result = markdown.parse("**Жирный** и *курсив*\n").children[0]
        self.assertIsInstance(result, Paragraph)
        # Проверяем, что дети содержат StrongEmphasis и Emphasis
        child_types = [type(c).__name__ for c in result.children]
        self.assertIn("StrongEmphasis", child_types)
        self.assertIn("Emphasis", child_types)
