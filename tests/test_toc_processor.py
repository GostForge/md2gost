"""Tests for TOC numbering behavior."""

import unittest

import docx

from md2gost.renderable.toc import ToC


class TestTocNumbering(unittest.TestCase):
    def test_unnumbered_heading_does_not_increment(self):
        doc = docx.Document()
        toc = ToC(doc._body)

        toc.add_item(1, "Intro", False, "a1")
        self.assertEqual(toc._numbering[0], 0)

        toc.add_item(1, "Chapter", True, "a2")
        self.assertEqual(toc._numbering[0], 1)
