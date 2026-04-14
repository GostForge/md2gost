from typing import Generator
from uuid import uuid4

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import CT_Tbl
from docx.shared import Pt, Twips
from docx.table import Table
from docx.text.paragraph import Paragraph as DocxParagraph

from .caption import CaptionInfo
from .requires_numbering import RequiresNumbering
from ..config import Md2GostConfig, get_default_config
from ..layout_tracker import LayoutState
from ..renderable import Renderable
from ..rendered_info import RenderedInfo
from ..util import create_element
from ..latex_math import latex_to_omml


class Equation(Renderable, RequiresNumbering):
    def __init__(
        self,
        parent,
        latex_formula: str,
        caption_info: CaptionInfo,
        config: Md2GostConfig | None = None,
    ):
        self._config = config or get_default_config()
        unique_name = caption_info.unique_name if caption_info and caption_info.unique_name else ""
        super().__init__(self._config.caption_equation, unique_name)
        word_math = latex_to_omml(latex_formula)

        sect = parent.part.document.sections[-1]

        # todo: style inheritance
        left_margin = Twips(int(parent.part.styles[self._config.style_normal_table]._element.xpath("w:tblPr/w:tblCellMar/w:left")[0].attrib["{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"]))
        right_margin = Twips(int(parent.part.styles[self._config.style_normal_table]._element.xpath("w:tblPr/w:tblCellMar/w:right")[0].attrib["{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"]))

        table_width = sect.page_width - sect.right_margin - sect.left_margin + left_margin + right_margin

        self._table = table = Table(CT_Tbl.new_tbl(1, 2, table_width), parent)

        left_cell = table.cell(0,0)
        right_cell = table.cell(0,1)
        right_cell.width = self._config.equation_number_width
        left_cell.width = table_width - right_cell.width

        table.rows[0].height = self._config.equation_height  # TODO: implement proper size

        left_paragraph = left_cell.paragraphs[0]
        left_paragraph.style = self._config.style_formula_content
        left_paragraph._p.append(word_math)
        left_cell.vertical_alignment = \
            WD_CELL_VERTICAL_ALIGNMENT.CENTER

        uid = uuid4().hex

        right_paragraph = right_cell.paragraphs[0]
        right_paragraph.style = self._config.style_formula_numbering
        right_paragraph._p.append(create_element("w:r", "("))
        if caption_info and caption_info.unique_name:
            right_paragraph._p.append(create_element("w:bookmarkStart", {
                "w:id": uid,
                "w:name": caption_info.unique_name
            }))
        self._numbering_run = create_element("w:r", "?")
        right_paragraph._p.append(
            create_element("w:fldSimple", {
                "w:instr": f"SEQ {self._config.caption_equation} \\* ARABIC"
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
        blank_height = Pt(self._config.font_size_main * self._config.line_spacing / Pt(1))
        yield RenderedInfo(blank_before, blank_height)

        height = self._config.equation_height

        if height > layout_state.remaining_page_height:
            height += layout_state.remaining_page_height

        yield RenderedInfo(self._table, height)

        # ГОСТ п. 5.2: после формулы — одна пустая строка
        blank_after = DocxParagraph(create_element("w:p"), self._table._tbl.getparent() or self._table._tbl)
        blank_after.paragraph_format.space_before = 0
        blank_after.paragraph_format.space_after = 0
        yield RenderedInfo(blank_after, blank_height)
