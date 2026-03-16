from copy import copy
from dataclasses import dataclass
from typing import Generator
from uuid import uuid4

from docx.shared import Parented, Cm
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.table import Table

from ..layout_tracker import LayoutState
from .renderable import Renderable
from ..rendered_info import RenderedInfo
from .paragraph_sizer import ParagraphSizer
from ..util import create_element
from ..constants import (
    STYLE_CAPTION, CAPTION_SEPARATOR, SPACE_BEFORE_CAPTION_AFTER_TABLE,
    CAPTION_FONT_SIZE, ORPHAN_CONTROL_LINES,
)

from docx.shared import Length


@dataclass
class CaptionInfo:
    unique_name: str
    text: str | None


def _make_rPr(bold: bool, italic: bool, sz_val: str):
    """Build a ``w:rPr`` element with bold / italic / size."""
    rPr = create_element("w:rPr")
    if bold:
        rPr.append(create_element("w:b"))
    else:
        rPr.append(create_element("w:b", {"w:val": "0"}))
    if italic:
        rPr.append(create_element("w:i"))
    else:
        rPr.append(create_element("w:i", {"w:val": "0"}))
    rPr.append(create_element("w:sz", {"w:val": sz_val}))
    rPr.append(create_element("w:szCs", {"w:val": sz_val}))
    return rPr


class Caption(Renderable):
    def __init__(self, parent: Parented, category: str, caption_info: CaptionInfo | None,
                 number: int | str = None, before=True, *,
                 is_bold: bool = None, is_italic: bool = None,
                 space_before: Length = None, space_after: Length = None):
        """
        Args:
            is_bold: Принудительно полужирный (ГОСТ: рисунки).
            is_italic: Принудительно курсив (ГОСТ: таблицы).
            space_before: Интервал перед caption (ГОСТ: 6пт для таблиц/листингов, 0 для рисунков).
            space_after: Интервал после caption (ГОСТ: 0 для таблиц/листингов, 6пт для рисунков).
        """
        self._parent = parent
        self._before = before
        self._space_before = space_before
        self._docx_paragraph = DocxParagraph(create_element("w:p"), parent)

        uid = uuid4().hex

        self._docx_paragraph.style = STYLE_CAPTION

        # ГОСТ per-type spacing (default: inherit from style)
        if space_after is not None:
            self._docx_paragraph.paragraph_format.space_after = space_after

        # Explicit values — never None so Template.docx style inheritance cannot interfere.
        # ГОСТ: рисунки=bold, таблицы/листинги=italic; все caption 12 пт.
        bold = bool(is_bold)
        italic = bool(is_italic)
        # half-points for raw XML runs (w:sz): Pt(12) = 24 hp
        sz_val = str(int(CAPTION_FONT_SIZE.pt * 2))

        # Первый run: "Категория "
        run_category = self._docx_paragraph.add_run(f"{category} ")
        run_category.bold = bold
        run_category.italic = italic
        run_category.font.size = CAPTION_FONT_SIZE

        if caption_info and caption_info.unique_name:
            self._docx_paragraph._p.append(create_element("w:bookmarkStart", {
                "w:id": uid,
                "w:name": caption_info.unique_name
            }))

        # --- Complex field: begin / instrText / separate / result / end ---
        # Using complex field chars instead of w:fldSimple so that Word/LO
        # preserves rPr (bold/italic/size) when recalculating SEQ fields.
        field_instr = f" SEQ {category} \\* ARABIC "

        # begin run
        r_begin = create_element("w:r", [_make_rPr(bold, italic, sz_val),
                                          create_element("w:fldChar", {"w:fldCharType": "begin"})])
        self._docx_paragraph._p.append(r_begin)

        # instrText run
        instr_elem = create_element("w:instrText", field_instr)
        instr_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r_instr = create_element("w:r", [_make_rPr(bold, italic, sz_val), instr_elem])
        self._docx_paragraph._p.append(r_instr)

        # separate run
        r_sep = create_element("w:r", [_make_rPr(bold, italic, sz_val),
                                        create_element("w:fldChar", {"w:fldCharType": "separate"})])
        self._docx_paragraph._p.append(r_sep)

        # result run (cached number value)
        self._numbering_run = create_element("w:r", [
            _make_rPr(bold, italic, sz_val),
            create_element("w:t", str(number) if number else "?"),
        ])
        self._docx_paragraph._p.append(self._numbering_run)

        # end run
        r_end = create_element("w:r", [_make_rPr(bold, italic, sz_val),
                                        create_element("w:fldChar", {"w:fldCharType": "end"})])
        self._docx_paragraph._p.append(r_end)

        if caption_info and caption_info.unique_name:
            self._docx_paragraph._p.append(create_element("w:bookmarkEnd", {
                "w:id": uid
            }))
        if caption_info and caption_info.text:
            run_text = self._docx_paragraph.add_run(f"{CAPTION_SEPARATOR}{caption_info.text}")
            run_text.bold = bold
            run_text.italic = italic
            run_text.font.size = CAPTION_FONT_SIZE

    def center(self):
        self._docx_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    def render(self, previous_rendered: RenderedInfo, layout_state: LayoutState) -> Generator[
            "RenderedInfo | Renderable", None, None]:
        if previous_rendered and isinstance(previous_rendered.docx_element, Table) \
                and not (layout_state.current_page_height == 0 and layout_state.page != 1):
            self._docx_paragraph.paragraph_format.space_before = SPACE_BEFORE_CAPTION_AFTER_TABLE
        elif self._space_before is not None:
            self._docx_paragraph.paragraph_format.space_before = self._space_before
        else:
            self._docx_paragraph.paragraph_format.space_before = None

        height_data = ParagraphSizer(
            self._docx_paragraph,
            previous_rendered.docx_element
            if previous_rendered and isinstance(previous_rendered.docx_element, DocxParagraph) else None,
            layout_state.max_width
        ).calculate_height()

        # if three more lines don't fit, move it to the next page (so there is no only caption on the end of the page)
        if self._before and ((height_data.lines + ORPHAN_CONTROL_LINES - 1) * height_data.line_spacing + 1) * height_data.line_height \
                > layout_state.remaining_page_height:
            self._docx_paragraph.paragraph_format.page_break_before = True
            self._docx_paragraph.paragraph_format.space_before = None
            height_data = ParagraphSizer(
                self._docx_paragraph,
                None,
                layout_state.max_width
            ).calculate_height()

        yield RenderedInfo(
            self._docx_paragraph,
            height_data.full +
            (layout_state.remaining_page_height
                if self._docx_paragraph.paragraph_format.page_break_before else 0))
