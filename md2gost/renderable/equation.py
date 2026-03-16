from typing import Generator
from uuid import uuid4

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import CT_Tbl
from docx.shared import Pt, Twips
from docx.table import Table
from docx.text.paragraph import Paragraph as DocxParagraph

from .caption import CaptionInfo
from .requires_numbering import RequiresNumbering
from ..layout_tracker import LayoutState
from ..renderable import Renderable
from ..rendered_info import RenderedInfo
from ..util import create_element
from ..latex_math import latex_to_omml
from ..constants import (
    EQUATION_DEFAULT_HEIGHT,
    EQUATION_NUMBER_CELL_WIDTH,
    EQUATION_CAPTION_CATEGORY,
    STYLE_FORMULA_CONTENT,
    STYLE_FORMULA_NUMBERING,
    STYLE_NORMAL_TABLE,
    FONT_SIZE_MAIN,
    LINE_SPACING_MAIN,
)


class Equation(Renderable, RequiresNumbering):
    def __init__(self, parent, latex_formula: str, caption_info: CaptionInfo):
        super().__init__(EQUATION_CAPTION_CATEGORY, caption_info.unique_name if caption_info else None)
        word_math = latex_to_omml(latex_formula)

        sect = parent.part.document.sections[-1]

        # todo: style inheritance
        left_margin = Twips(int(parent.part.styles[STYLE_NORMAL_TABLE]._element.xpath("w:tblPr/w:tblCellMar/w:left")[0].attrib["{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"]))
        right_margin = Twips(int(parent.part.styles[STYLE_NORMAL_TABLE]._element.xpath("w:tblPr/w:tblCellMar/w:right")[0].attrib["{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"]))

        table_width = sect.page_width - sect.right_margin - sect.left_margin + left_margin + right_margin

        self._table = table = Table(CT_Tbl.new_tbl(1, 2, table_width), parent)

        left_cell = table.cell(0,0)
        right_cell = table.cell(0,1)
        right_cell.width = EQUATION_NUMBER_CELL_WIDTH
        left_cell.width = table_width - right_cell.width

        table.rows[0].height = EQUATION_DEFAULT_HEIGHT  # TODO: implement proper size

        left_paragraph = left_cell.paragraphs[0]
        left_paragraph.style = STYLE_FORMULA_CONTENT
        left_paragraph._p.append(word_math)
        left_cell.vertical_alignment = \
            WD_CELL_VERTICAL_ALIGNMENT.CENTER

        uid = uuid4().hex

        right_paragraph = right_cell.paragraphs[0]
        right_paragraph.style = STYLE_FORMULA_NUMBERING
        right_paragraph._p.append(create_element("w:r", "("))
        if caption_info and caption_info.unique_name:
            right_paragraph._p.append(create_element("w:bookmarkStart", {
                "w:id": uid,
                "w:name": caption_info.unique_name
            }))
        self._numbering_run = create_element("w:r", "?")
        right_paragraph._p.append(
            create_element("w:fldSimple", {
                "w:instr": f"SEQ {EQUATION_CAPTION_CATEGORY} \\* ARABIC"
            }, [self._numbering_run]))
        if caption_info and caption_info.unique_name:
            right_paragraph._p.append(create_element("w:bookmarkEnd", {
                "w:id": uid
            }))
        right_paragraph._p.append(create_element("w:r", ")"))
        right_cell.vertical_alignment = \
            WD_CELL_VERTICAL_ALIGNMENT.CENTER

    def set_number(self, number: int | str):
        self._numbering_run.text = str(number)

    def render(self, previous_rendered: RenderedInfo, layout_state: LayoutState) -> Generator[
            "RenderedInfo | Renderable", None, None]:
        # ГОСТ п. 5.2: перед формулой — одна пустая строка
        blank_before = DocxParagraph(create_element("w:p"), self._table._tbl.getparent() or self._table._tbl)
        blank_before.paragraph_format.space_before = 0
        blank_before.paragraph_format.space_after = 0
        blank_before.runs  # force init
        blank_height = Pt(FONT_SIZE_MAIN * LINE_SPACING_MAIN / Pt(1))
        yield RenderedInfo(blank_before, blank_height)

        height = EQUATION_DEFAULT_HEIGHT

        if height > layout_state.remaining_page_height:
            height += layout_state.remaining_page_height

        yield RenderedInfo(self._table, height)

        # ГОСТ п. 5.2: после формулы — одна пустая строка
        blank_after = DocxParagraph(create_element("w:p"), self._table._tbl.getparent() or self._table._tbl)
        blank_after.paragraph_format.space_before = 0
        blank_after.paragraph_format.space_after = 0
        yield RenderedInfo(blank_after, blank_height)
