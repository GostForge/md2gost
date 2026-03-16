"""Тесты для RenderableFactory — создание Renderable из marko-элементов."""

import unittest
from pathlib import Path

import docx

from md2gost.extended_markdown import markdown
from md2gost.renderable_factory import RenderableFactory
from md2gost.renderable.paragraph import Paragraph
from md2gost.renderable.heading import Heading
from md2gost.renderable.list import List
from md2gost.renderable.listing import Listing
from md2gost.renderable.table import Table
from md2gost.renderable.equation import Equation
from md2gost.renderable.toc import ToC
from md2gost.renderable.image import Image
from md2gost.renderable.caption import CaptionInfo


def _make_factory():
    template_path = Path(__file__).resolve().parents[1] / "md2gost" / "Template.docx"
    doc = docx.Document(str(template_path))
    return RenderableFactory(doc._body), doc


class TestFactoryParagraph(unittest.TestCase):
    def test_creates_paragraph(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("Простой текст.\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Paragraph)


class TestFactoryHeading(unittest.TestCase):
    def test_creates_heading(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("# Заголовок\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Heading)

    def test_heading_level(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("### Пункт\n")
        heading = list(factory.create(parsed.children[0], None))[0]
        self.assertEqual(heading.level, 3)

    def test_unnumbered_heading(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("# *Содержание\n")
        heading = list(factory.create(parsed.children[0], None))[0]
        self.assertFalse(heading.is_numbered)


class TestFactoryList(unittest.TestCase):
    def test_creates_unordered_list(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("- Первый\n- Второй\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], List)

    def test_creates_ordered_list(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("1. Первый\n2. Второй\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], List)


class TestFactoryListing(unittest.TestCase):
    def test_creates_listing(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("```python\nprint('x')\n```\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Listing)


class TestFactoryTable(unittest.TestCase):
    def test_creates_table(self):
        factory, doc = _make_factory()
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        parsed = markdown.parse(md)
        caption_info = CaptionInfo("test_table", "Тестовая таблица")
        results = list(factory.create(parsed.children[0], caption_info))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Table)


class TestFactoryEquation(unittest.TestCase):
    def test_creates_equation(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("$$ x^2 + 1 $$\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Equation)


class TestFactoryTOC(unittest.TestCase):
    def test_creates_toc(self):
        factory, doc = _make_factory()
        parsed = markdown.parse("[TOC]\n")
        results = list(factory.create(parsed.children[0], None))
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ToC)
