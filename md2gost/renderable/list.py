from copy import copy
from typing import Generator

from . import Paragraph
from .renderable import Renderable
from ..config import Md2GostConfig, get_default_config
from ..layout_tracker import LayoutState
from ..rendered_info import RenderedInfo


class List(Renderable):
    def __init__(self, parent, ordered: bool, config: Md2GostConfig | None = None):
        self._parent = parent
        self._ordered = ordered
        self._config = config or get_default_config()
        self._paragraphs: list[Paragraph] = []
        self._last_paragraph_space_after = 0

        self._numbering = [0 for _ in range(10)]

    def add_item(self, level: int) -> Paragraph:
        if level < 1 or level > len(self._numbering):
            raise ValueError(f"Неподдерживаемый уровень списка: {level}")

        self._numbering[level - 1] += 1
        for i in range(level, len(self._numbering)):
            self._numbering[i] = 0

        paragraph = Paragraph(self._parent)
        marker = f"{self._numbering[level-1]}." if self._ordered else self._config.list_marker
        paragraph.add_run(f"{marker}\t")

        # ГОСТ Таблица 4.1: маркер на 1.25 см, текст на 2.25 см
        # first_indent (from Normal) = 1.25 см — позиция маркера
        first_indent = self._parent.part.styles[self._config.style_normal].paragraph_format.first_line_indent or 0

        # left_indent = позиция текста. Уровень 1: first_indent + LIST_MARKER_INDENT
        paragraph._docx_paragraph.paragraph_format.tab_stops.add_tab_stop(
            max(self._config.list_marker_indent, self._config.list_tab_stop)
        )
        paragraph._docx_paragraph.paragraph_format.left_indent = (
            first_indent + self._config.list_marker_indent + self._config.list_level_indent * (level - 1)
        )
        # Hanging indent: маркер смещается назад на LIST_MARKER_INDENT
        paragraph._docx_paragraph.paragraph_format.first_line_indent = -self._config.list_marker_indent

        self._last_paragraph_space_after = paragraph._docx_paragraph.paragraph_format.space_after
        paragraph._docx_paragraph.paragraph_format.space_before = 0
        paragraph._docx_paragraph.paragraph_format.space_after = 0

        self._paragraphs.append(paragraph)
        return paragraph

    def render(self, previous_rendered: RenderedInfo, layout_state: LayoutState) -> Generator[
            RenderedInfo | Renderable, None, None]:
        self._paragraphs[-1]._docx_paragraph.paragraph_format.space_after = self._last_paragraph_space_after

        for paragraph in self._paragraphs:
            for rendered in paragraph.render(previous_rendered, copy(layout_state)):
                if not isinstance(rendered, RenderedInfo):
                    continue
                layout_state.add_height(rendered.height)
                previous_rendered = rendered
                yield rendered
