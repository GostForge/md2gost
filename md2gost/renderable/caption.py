from copy import copy
from dataclasses import dataclass
from typing import Generator
from uuid import uuid4

from docx.shared import Parented
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.table import Table

from ..config import Md2GostConfig, get_default_config
from ..layout_tracker import LayoutState
from .renderable import Renderable
from ..rendered_info import RenderedInfo
from .paragraph_sizer import ParagraphSizer
from ..util import create_element
from ..config import CaptionTextStyle

from docx.shared import Length


_ATTR_W_VAL = "w:val"
_ELEM_FLD_CHAR = "w:fldChar"
_ATTR_FLD_CHAR_TYPE = "w:fldCharType"


@dataclass
class CaptionInfo:
    unique_name: str
    text: str | None


def _make_r_pr(bold: bool, italic: bool, underline: bool, sz_val: str):
    """Build a ``w:rPr`` element with bold / italic / size."""
    r_pr = create_element("w:rPr")
    if bold:
        r_pr.append(create_element("w:b"))
    else:
        r_pr.append(create_element("w:b", {_ATTR_W_VAL: "0"}))
    if italic:
        r_pr.append(create_element("w:i"))
    else:
        r_pr.append(create_element("w:i", {_ATTR_W_VAL: "0"}))
    if underline:
        r_pr.append(create_element("w:u", {_ATTR_W_VAL: "single"}))
    else:
        r_pr.append(create_element("w:u", {_ATTR_W_VAL: "none"}))
    r_pr.append(create_element("w:sz", {_ATTR_W_VAL: sz_val}))
    r_pr.append(create_element("w:szCs", {_ATTR_W_VAL: sz_val}))
    return r_pr


def _style_for_category(category: str, config: Md2GostConfig) -> CaptionTextStyle:
    if category == config.caption_table:
        return config.caption_table_style
    if category == config.caption_image:
        return config.caption_image_style
    if category == config.caption_listing:
        return config.caption_listing_style
    if category == config.caption_equation:
        return config.caption_equation_style
    return CaptionTextStyle.NONE


class Caption(Renderable):
    def __init__(self, parent: Parented, category: str, caption_info: CaptionInfo | None,
                 number: int | str = None, before=True, *,
                 is_bold: bool = None, is_italic: bool = None,
                 is_underline: bool = None,
                 text_style: CaptionTextStyle | None = None,
                 config: Md2GostConfig | None = None,
                 space_before: Length = None, space_after: Length = None):
        """
        Args:
            is_bold: Принудительно полужирный (ГОСТ: рисунки).
            is_italic: Принудительно курсив (ГОСТ: таблицы).
            is_underline: Принудительное подчёркивание.
            text_style: Декорации подписи через bit flags CaptionTextStyle.
            space_before: Интервал перед caption (ГОСТ: 6пт для таблиц/листингов, 0 для рисунков).
            space_after: Интервал после caption (ГОСТ: 0 для таблиц/листингов, 6пт для рисунков).
        """
        self._parent = parent
        self._before = before
        self._space_before = space_before
        self._config = config or get_default_config()
        self._docx_paragraph = DocxParagraph(create_element("w:p"), parent)

        uid = uuid4().hex

        self._docx_paragraph.style = self._config.style_caption

        # ГОСТ per-type spacing (default: inherit from style)
        if space_after is not None:
            self._docx_paragraph.paragraph_format.space_after = space_after

        # Explicit values — never None so Template.docx style inheritance cannot interfere.
        # ГОСТ: рисунки=bold, таблицы/листинги=italic; все caption 12 пт.
        if text_style is None:
            if is_bold is None and is_italic is None and is_underline is None:
                text_style = _style_for_category(category, self._config)
            else:
                text_style = CaptionTextStyle.NONE
                if bool(is_bold):
                    text_style |= CaptionTextStyle.BOLD
                if bool(is_italic):
                    text_style |= CaptionTextStyle.ITALIC
                if bool(is_underline):
                    text_style |= CaptionTextStyle.UNDERLINE

        bold = bool(text_style & CaptionTextStyle.BOLD)
        italic = bool(text_style & CaptionTextStyle.ITALIC)
        underline = bool(text_style & CaptionTextStyle.UNDERLINE)
        # half-points for raw XML runs (w:sz): Pt(12) = 24 hp
        sz_val = str(int(self._config.caption_font_size.pt * 2))

        # Первый run: "Категория "
        run_category = self._docx_paragraph.add_run(f"{category} ")
        run_category.bold = bold
        run_category.italic = italic
        run_category.underline = underline
        run_category.font.size = self._config.caption_font_size

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
        r_begin = create_element("w:r", [_make_r_pr(bold, italic, underline, sz_val),
                          create_element(_ELEM_FLD_CHAR, {_ATTR_FLD_CHAR_TYPE: "begin"})])
        self._docx_paragraph._p.append(r_begin)

        # instrText run
        instr_elem = create_element("w:instrText", field_instr)
        instr_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r_instr = create_element("w:r", [_make_r_pr(bold, italic, underline, sz_val), instr_elem])
        self._docx_paragraph._p.append(r_instr)

        # separate run
        r_sep = create_element("w:r", [_make_r_pr(bold, italic, underline, sz_val),
                        create_element(_ELEM_FLD_CHAR, {_ATTR_FLD_CHAR_TYPE: "separate"})])
        self._docx_paragraph._p.append(r_sep)

        # result run (cached number value)
        self._numbering_run = create_element("w:r", [
            _make_r_pr(bold, italic, underline, sz_val),
            create_element("w:t", str(number) if number else "?"),
        ])
        self._docx_paragraph._p.append(self._numbering_run)

        # end run
        r_end = create_element("w:r", [_make_r_pr(bold, italic, underline, sz_val),
                                        create_element(_ELEM_FLD_CHAR, {_ATTR_FLD_CHAR_TYPE: "end"})])
        self._docx_paragraph._p.append(r_end)

        if caption_info and caption_info.unique_name:
            self._docx_paragraph._p.append(create_element("w:bookmarkEnd", {
                "w:id": uid
            }))
        if caption_info and caption_info.text:
            run_text = self._docx_paragraph.add_run(f"{self._config.caption_separator}{caption_info.text}")
            run_text.bold = bold
            run_text.italic = italic
            run_text.underline = underline
            run_text.font.size = self._config.caption_font_size

    def center(self):
        self._docx_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    def render(self, previous_rendered: RenderedInfo, layout_state: LayoutState) -> Generator[
            "RenderedInfo | Renderable", None, None]:
        if previous_rendered and isinstance(previous_rendered.docx_element, Table) \
                and not (layout_state.current_page_height == 0 and layout_state.page != 1):
            self._docx_paragraph.paragraph_format.space_before = self._config.space_before_caption_after_table
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
        if self._before and ((height_data.lines + self._config.orphan_control_lines - 1) * height_data.line_spacing + 1) * height_data.line_height \
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
