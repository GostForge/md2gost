from copy import copy
from typing import Generator

from docx.shared import Pt, Cm, Twips

from . import Paragraph
from .renderable import Renderable
from ..constants import (
    LIST_LEVEL_INDENT as LEVEL_INDENT,
    LIST_MARKER_INDENT,
    LIST_TAB_STOP,
    LIST_MARKER_UNORDERED,
    STYLE_NORMAL,
)
from ..layout_tracker import LayoutState
from ..rendered_info import RenderedInfo


class List(Renderable):
    def __init__(self, parent, ordered: bool):
        self._parent = parent
        self._ordered = ordered
        self._paragraphs: list[Paragraph] = []
        self._last_paragraph_space_after = 0

        self._numbering = [0 for _ in range(10)]

    def add_item(self, level: int) -> Paragraph:
        self._numbering[level - 1] += 1
        for i in range(level, len(self._numbering)):
            self._numbering[i] = 0

        paragraph = Paragraph(self._parent)
        paragraph.add_run((f"{self._numbering[level-1]}." if self._ordered else LIST_MARKER_UNORDERED)+"\t")

        # ГОСТ Таблица 4.1: маркер на 1.25 см, текст на 2.25 см
        # first_indent (from Normal) = 1.25 см — позиция маркера
        first_indent = self._parent.part.styles[STYLE_NORMAL].paragraph_format.first_line_indent or 0

        # left_indent = позиция текста. Уровень 1: first_indent + LIST_MARKER_INDENT
        paragraph._docx_paragraph.paragraph_format.tab_stops.add_tab_stop(LIST_TAB_STOP)
        paragraph._docx_paragraph.paragraph_format.left_indent = (
            first_indent + LIST_MARKER_INDENT + LEVEL_INDENT * (level - 1)
        )
        # Hanging indent: маркер смещается назад на LIST_MARKER_INDENT
        paragraph._docx_paragraph.paragraph_format.first_line_indent = -LIST_MARKER_INDENT

        self._last_paragraph_space_after = paragraph._docx_paragraph.paragraph_format.space_after
        paragraph._docx_paragraph.paragraph_format.space_before = 0
        paragraph._docx_paragraph.paragraph_format.space_after = 0

        self._paragraphs.append(paragraph)
        return paragraph

    def render(self, previous_rendered: RenderedInfo, layout_state: LayoutState) -> Generator[
            RenderedInfo | Renderable, None, None]:
        self._paragraphs[-1]._docx_paragraph.paragraph_format.space_after = self._last_paragraph_space_after

        for paragraph in self._paragraphs:
            for x in paragraph.render(previous_rendered, copy(layout_state)):
                layout_state.add_height(x.height)
                previous_rendered = x
                yield x
