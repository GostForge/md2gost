"""
Конфигурация md2gost — параметры, которые пользователь может менять.

Все значения по умолчанию соответствуют ГОСТ. Переопределить можно через:
  1. Аргументы конструктора Md2GostConfig(...)
  2. (Будущее) YAML/JSON конфиг-файл
  3. (Будущее) CLI-аргументы
"""

from __future__ import annotations

from dataclasses import dataclass
from docx.shared import Length

from . import constants as C


@dataclass
class Md2GostConfig:
    """Конфигурационный объект md2gost.

    Позволяет переопределять параметры, не трогая ни Template.docx, ни код.
    Все значения по умолчанию === ГОСТ.
    """

    # ── Поля страницы ────────────────────────────────────────────────────
    page_margin_left: Length = C.PAGE_MARGIN_LEFT
    page_margin_right: Length = C.PAGE_MARGIN_RIGHT
    page_margin_top: Length = C.PAGE_MARGIN_TOP
    page_margin_bottom: Length = C.PAGE_MARGIN_BOTTOM

    # ── Основной текст ──────────────────────────────────────────────────
    font_main: str = C.FONT_MAIN
    font_size_main: Length = C.FONT_SIZE_MAIN
    line_spacing: float = C.LINE_SPACING_MAIN
    first_line_indent: Length = C.FIRST_LINE_INDENT

    # ── Листинги ────────────────────────────────────────────────────────
    font_code: str = C.FONT_CODE
    font_size_code: Length = C.FONT_SIZE_CODE
    syntax_highlighting: bool = False

    # ── Списки ──────────────────────────────────────────────────────────
    list_marker: str = C.LIST_MARKER_UNORDERED
    list_marker_indent: Length = C.LIST_MARKER_INDENT
    list_level_indent: Length = C.LIST_LEVEL_INDENT

    # ── Captions ────────────────────────────────────────────────────────
    caption_separator: str = C.CAPTION_SEPARATOR
    # Категории можно переименовать (например, «Рис.» вместо «Рисунок»)
    caption_table: str = C.TABLE_CAPTION_CATEGORY
    caption_image: str = C.IMAGE_CAPTION_CATEGORY
    caption_listing: str = C.LISTING_CAPTION_CATEGORY
    caption_equation: str = C.EQUATION_CAPTION_CATEGORY
    # Оформление подписей через bit flags (можно комбинировать через |)
    caption_table_style: C.CaptionTextStyle = C.TABLE_CAPTION_TEXT_STYLE_DEFAULT
    caption_image_style: C.CaptionTextStyle = C.IMAGE_CAPTION_TEXT_STYLE_DEFAULT
    caption_listing_style: C.CaptionTextStyle = C.LISTING_CAPTION_TEXT_STYLE_DEFAULT
    caption_equation_style: C.CaptionTextStyle = C.EQUATION_CAPTION_TEXT_STYLE_DEFAULT

    # ── Продолжения при переносе ────────────────────────────────────────
    table_continuation: str = C.TABLE_CONTINUATION_PREFIX
    listing_continuation: str = C.LISTING_CONTINUATION_PREFIX

    # ── Формулы ─────────────────────────────────────────────────────────
    equation_height: Length = C.EQUATION_DEFAULT_HEIGHT
    equation_number_width: Length = C.EQUATION_NUMBER_CELL_WIDTH

    # ── Нумерация ───────────────────────────────────────────────────────
    # True = посекционная нумерация (Рисунок 2.3), False = сквозная (Рисунок 3)
    sectional_numbering: bool = False  # TODO: переключить на True после реализации

    # ── Титульная страница ──────────────────────────────────────────────
    title_pages: int = 1

    # ── Отладка ─────────────────────────────────────────────────────────
    debug: bool = False


# Синглтон по умолчанию — используется, если config не передан явно
_default_config: Md2GostConfig | None = None


def get_default_config() -> Md2GostConfig:
    """Вернуть глобальный конфиг (создаёт при первом вызове)."""
    global _default_config
    if _default_config is None:
        _default_config = Md2GostConfig()
    return _default_config


def set_default_config(config: Md2GostConfig) -> None:
    """Установить глобальный конфиг (полезно для тестов и сервера)."""
    global _default_config
    _default_config = config
