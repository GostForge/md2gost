"""ГОСТ-константы и магические числа md2gost.

Единый стиль: параметры сгруппированы по доменным категориям.
Источник: OUT.md (правила оформления по ГОСТ).
"""

from enum import IntFlag, auto

from docx.shared import Cm, Mm, Pt


class CaptionTextStyle(IntFlag):
    """Bit flags for caption text decoration.

    Пример комбинирования:
      CaptionTextStyle.BOLD | CaptionTextStyle.UNDERLINE
    """

    NONE = 0
    BOLD = auto()
    ITALIC = auto()
    UNDERLINE = auto()


# ─── Страницы / Layout ──────────────────────────────────────────────────────
PAGE_WIDTH_A4 = Mm(210)            # Ширина страницы A4
PAGE_HEIGHT_A4 = Mm(297)           # Высота страницы A4

PAGE_MARGIN_LEFT = Cm(3.0)         # Левое поле: 30 мм
PAGE_MARGIN_RIGHT = Cm(1.0)        # Правое поле: 10 мм
PAGE_MARGIN_TOP = Cm(2.0)          # Верхнее поле: 20 мм
PAGE_MARGIN_BOTTOM = Cm(2.0)       # Нижнее поле: 20 мм

# NB: В Template.docx left_margin=2.50 cm и bottom_margin=1.25 cm.
# В converter.py используется это значение для расчёта рабочей высоты.
BOTTOM_MARGIN_EFFECTIVE = Cm(1.86)  # Эффективное нижнее поле для расчёта рабочей высоты


# ─── Основной текст ─────────────────────────────────────────────────────────
FONT_MAIN = "Times New Roman"      # Базовый шрифт основного текста
FONT_SIZE_MAIN = Pt(14)             # Размер шрифта основного текста
LINE_SPACING_MAIN = 1.5             # Межстрочный интервал основного текста
LINE_SPACING_SINGLE = 1             # Одинарный интервал (служебные/внутритабличные абзацы)
FIRST_LINE_INDENT = Cm(1.25)        # Красная строка основного текста


# ─── Заголовки ──────────────────────────────────────────────────────────────
HEADING1_FONT_SIZE = Pt(18)         # Размер заголовка 1 уровня
HEADING1_SPACE_BEFORE = Pt(0)       # Интервал перед заголовком 1 уровня
HEADING1_SPACE_AFTER = Pt(12)       # Интервал после заголовка 1 уровня

HEADING2_FONT_SIZE = Pt(16)         # Размер заголовка 2 уровня
HEADING2_SPACE_BEFORE = Pt(24)      # Интервал перед заголовком 2 уровня
HEADING2_SPACE_AFTER = Pt(12)       # Интервал после заголовка 2 уровня

HEADING3_FONT_SIZE = Pt(14)         # Размер заголовка 3+ уровня
HEADING3_SPACE_BEFORE = Pt(24)      # Интервал перед заголовком 3+ уровня
HEADING3_SPACE_AFTER = Pt(12)       # Интервал после заголовка 3+ уровня


# ─── Подписи: общие параметры ──────────────────────────────────────────────
CAPTION_FONT_SIZE = Pt(12)          # Базовый размер шрифта подписи
CAPTION_SEPARATOR = " \u2014 "      # Разделитель между номером и текстом подписи


# ─── Таблицы ────────────────────────────────────────────────────────────────
TABLE_CAPTION_CATEGORY = "Таблица"                                # Название категории подписи таблицы
TABLE_CAPTION_TEXT_STYLE_DEFAULT = CaptionTextStyle.ITALIC        # Декорация подписи таблицы по умолчанию
TABLE_CAPTION_SPACE_BEFORE = Pt(6)                                # Интервал перед подписью таблицы
TABLE_CAPTION_SPACE_AFTER = Pt(0)                                 # Интервал после подписи таблицы

TABLE_CONTENT_FONT_SIZE = Pt(12)                                  # Размер шрифта текста внутри таблицы
TABLE_CELL_OFFSET = Pt(10)                                        # Компенсация внутреннего padding ячейки
TABLE_BORDER_HEIGHT = Pt(0.5)                                     # Высота одной горизонтальной границы таблицы
TABLE_CONTINUATION_PREFIX = "Продолжение Таблицы"                 # Префикс при переносе таблицы

# Интервалы контекста таблицы
SPACE_AFTER_TABLE = Cm(0.35)                                      # Интервал перед абзацем, следующим за таблицей
SPACE_BEFORE_CAPTION_AFTER_TABLE = Cm(0.45)                       # Интервал перед подписью, идущей после таблицы


# ─── Рисунки ────────────────────────────────────────────────────────────────
IMAGE_CAPTION_CATEGORY = "Рисунок"                                # Название категории подписи рисунка
IMAGE_CAPTION_TEXT_STYLE_DEFAULT = CaptionTextStyle.BOLD          # Декорация подписи рисунка по умолчанию
IMAGE_CAPTION_SPACE_BEFORE = Pt(0)                                # Интервал перед подписью рисунка
IMAGE_CAPTION_SPACE_AFTER = Pt(6)                                 # Интервал после подписи рисунка

IMAGE_RESIZE_THRESHOLD = 0.7                                      # Порог сжатия изображения при нехватке места


# ─── Листинги ───────────────────────────────────────────────────────────────
LISTING_CAPTION_CATEGORY = "Листинг"                              # Название категории подписи листинга
LISTING_CAPTION_TEXT_STYLE_DEFAULT = CaptionTextStyle.ITALIC      # Декорация подписи листинга по умолчанию
LISTING_CAPTION_SPACE_BEFORE = Pt(6)                              # Интервал перед подписью листинга
LISTING_CAPTION_SPACE_AFTER = Pt(0)                               # Интервал после подписи листинга

FONT_CODE = "Courier New"                                         # Базовый шрифт кода в листингах
FONT_SIZE_CODE = Pt(10)                                           # Размер шрифта кода в листингах
LISTING_CONTINUATION_PREFIX = "Продолжение Листинга"              # Префикс при переносе листинга
LISTING_OFFSET = Pt(14)                                           # Компенсация внутреннего padding рамки листинга
LISTING_BORDER_HEIGHT = Pt(1)                                     # Суммарная высота верхней+нижней границы листинга
LISTING_PYGMENTS_STYLE = "sas"                                    # Цветовая схема подсветки Pygments


# ─── Формулы ────────────────────────────────────────────────────────────────
EQUATION_CAPTION_CATEGORY = "Формула"                             # Название категории нумерации формул
EQUATION_CAPTION_TEXT_STYLE_DEFAULT = CaptionTextStyle.NONE       # Декорация подписи формулы по умолчанию

EQUATION_DEFAULT_HEIGHT = Pt(50)                                  # Базовая высота строки формулы
EQUATION_NUMBER_CELL_WIDTH = Pt(30)                               # Ширина ячейки с номером формулы


# ─── Списки ─────────────────────────────────────────────────────────────────
LIST_MARKER_UNORDERED = "●"                                       # Маркер маркированного списка по умолчанию
LIST_MARKER_INDENT = Cm(1.0)                                      # Отступ от начала абзаца до маркера
LIST_LEVEL_INDENT = Cm(1.0)                                       # Дополнительный отступ на каждый уровень вложенности
LIST_TAB_STOP = Cm(1.0)                                           # Позиция таб-стопа после маркера


# ─── TOC ────────────────────────────────────────────────────────────────────
TOC_ENTRY_SPACE_AFTER = Cm(0.18)                                  # Интервал после строки в содержании
TOC_LEVEL_INDENT = "    "                                         # Строковый отступ на уровень вложенности TOC


# ─── Page layout heuristics ────────────────────────────────────────────────
ORPHAN_CONTROL_LINES = 3                                          # Минимум строк после заголовка/подписи до переноса страницы

# ParagraphSizer (эмпирика FreeType/docx)
LINE_HEIGHT_TIMES_14 = Pt(16.05)                                  # Эмпирическая высота строки Times New Roman 14
LINE_HEIGHT_COURIER_12 = Pt(13.61)                                # Эмпирическая высота строки Courier New 12
SPACE_WIDTH_CORRECTION = 0.81                                     # Поправка ширины пробела для non-mono шрифтов

# PageBreak
PAGE_BREAK_FONT_SIZE = Pt(1)                                      # Технический размер шрифта для невидимого page-break абзаца


# ─── Style names in Template.docx ───────────────────────────────────────────
STYLE_NORMAL = "Normal"                                           # Стиль основного абзаца
STYLE_HEADING_PREFIX = "Heading"                                  # Префикс стилей заголовков (Heading 1..9)
STYLE_CAPTION = "Caption"                                         # Стиль подписи
STYLE_CODE = "Code"                                               # Стиль абзаца кода
STYLE_TABLE_GRID = "Table Grid"                                   # Табличный стиль по умолчанию
STYLE_NORMAL_TABLE = "Normal Table"                               # Базовый стиль таблицы
STYLE_FORMULA_CONTENT = "Formula Content"                         # Стиль левой ячейки формулы
STYLE_FORMULA_NUMBERING = "Formula Numbering"                     # Стиль правой ячейки нумерации формулы
STYLE_HYPERLINK = "Hyperlink"                                     # Стиль гиперссылки
