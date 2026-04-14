import logging
from copy import copy
from typing import Generator
from urllib.parse import urlparse

from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Length, Parented
from docx.text.paragraph import Paragraph

from .caption import Caption, CaptionInfo
from .renderable import Renderable
from .requires_numbering import RequiresNumbering
from ..config import Md2GostConfig, get_default_config
from ..layout_tracker import LayoutState
from ..rendered_info import RenderedInfo
from ..util import create_element, public_path_for_warning
from ..warnings_collector import add_warning


_BLOCKED_PATH_TRAVERSAL = "__blocked_path_traversal__"
_BLOCKED_EXTERNAL_REFERENCE = "__blocked_external_reference__"


def _is_external_reference(path: str) -> bool:
    if not isinstance(path, str):
        return False
    parsed = urlparse(path)
    return bool(parsed.scheme) or path.startswith("//")


class Image(Renderable, RequiresNumbering):
    def __init__(
        self,
        parent: Parented,
        path: str,
        caption_info: CaptionInfo | None = None,
        source_path: str | None = None,
        config: Md2GostConfig | None = None,
    ):
        if not isinstance(path, str):
            path = str(path)

        self._config = config or get_default_config()
        unique_name = caption_info.unique_name if caption_info and caption_info.unique_name else ""
        super().__init__(self._config.caption_image, unique_name)
        self._parent = parent
        self._caption_info = caption_info
        warning_path = public_path_for_warning(source_path if source_path is not None else path)
        self._docx_paragraph = Paragraph(create_element("w:p"), parent)
        self._docx_paragraph.paragraph_format.space_before = 0
        self._docx_paragraph.paragraph_format.space_after = 0
        self._docx_paragraph.paragraph_format.first_line_indent = 0
        self._docx_paragraph.paragraph_format.line_spacing = self._config.line_spacing_single
        self._docx_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        self._invalid = False

        run = self._docx_paragraph.add_run()

        if path == _BLOCKED_EXTERNAL_REFERENCE or _is_external_reference(path):
            msg = f"Внешние URL картинок запрещены политикой безопасности: {warning_path}"
            logging.warning(msg)
            add_warning(msg)
            self._invalid = True
        elif path == _BLOCKED_PATH_TRAVERSAL:
            msg = f"Доступ к файлам вне рабочей директории запрещён: {warning_path}"
            logging.warning(msg)
            add_warning(msg)
            self._invalid = True
        else:
            try:
                self._image = run.add_picture(path)
            except FileNotFoundError:
                msg = f"Путь {warning_path} не существует, картинка не будет добавлена"
                logging.warning(msg)
                add_warning(msg)
                self._invalid = True

        self._number = None

    def set_number(self, number: int | str):
        self._number = number

    def resize(self, width: Length = None, height: Length = None):
        if not any((width, height)):
            return

        if not width:
            width = height * (self._image.width / self._image.height)

        if not height:
            height = width * (self._image.height / self._image.width)

        self._image.width = Length(width)
        self._image.height = Length(height)

    def render(
        self,
        previous_rendered: RenderedInfo,
        layout_state: LayoutState,
    ) -> Generator[RenderedInfo | Renderable, None, None]:
        if self._invalid:
            yield from []
            return

        if self._image.width > layout_state.max_width:
            self.resize(width=layout_state.max_width)

        if self._image.height > layout_state.max_height:
            self.resize(height=layout_state.max_height)

        height = self._image.height

        caption = Caption(
            self._parent,
            self._config.caption_image,
            self._caption_info,
            self._number,
            False,
            text_style=self._config.caption_image_style,
            config=self._config,
            space_before=self._config.caption_image_space_before,
            space_after=self._config.caption_image_space_after,
        )
        caption.center()

        caption_rendered_infos = list(caption.render(None, copy(layout_state)))
        caption_height = sum([info.height for info in caption_rendered_infos])

        if height + caption_height > layout_state.remaining_page_height:
            if height * self._config.image_resize_threshold <= (layout_state.remaining_page_height - caption_height):
                self.resize(height=layout_state.remaining_page_height - caption_height)
                height = layout_state.remaining_page_height - caption_height
            else:
                height += layout_state.remaining_page_height
                self._docx_paragraph.paragraph_format.page_break_before = True

        yield RenderedInfo(self._docx_paragraph, height)
        yield from caption_rendered_infos
