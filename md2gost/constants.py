"""
ГОСТ-константы и магические числа md2gost.

Все значения, захардкоженные ранее по разным файлам, собраны здесь.
Источник: OUT.md (Правила оформления курсовой работы / ВКР по ГОСТ).

Единицы измерения:
  - Размеры в docx хранятся в EMU (English Metric Units), 1 inch = 914400 EMU
  - Pt(1) = 12700 EMU, Cm(1) = 360000 EMU, Mm(1) = 36000 EMU, Twips(1) = 635 EMU
"""

from docx.shared import Pt, Cm, Mm, Twips


# ─── Поля страницы (ГОСТ п. 1.5) ────────────────────────────────────────────
PAGE_MARGIN_LEFT = Cm(3.0)        # Левое — 30 мм  (ГОСТ: 30 мм)
PAGE_MARGIN_RIGHT = Cm(1.0)       # Правое — 10 мм (ГОСТ: 10 мм)
PAGE_MARGIN_TOP = Cm(2.0)         # Верхнее — 20 мм (ГОСТ: 20 мм)
PAGE_MARGIN_BOTTOM = Cm(2.0)      # Нижнее — 20 мм  (ГОСТ: 20 мм)

# NB: В Template.docx left_margin=2.50 cm (а не 3.0!) и bottom_margin=1.25 cm.
# Код converter.py фактически использует BOTTOM_MARGIN_EFFECTIVE для расчёта
# высоты страницы (с учётом footer). Оригинальное значение: Cm(1.86).
BOTTOM_MARGIN_EFFECTIVE = Cm(1.86)

# ─── Размеры страницы A4 ────────────────────────────────────────────────────
PAGE_WIDTH_A4 = Mm(210)
PAGE_HEIGHT_A4 = Mm(297)


# ─── Основной текст (Таблица 1.1) ───────────────────────────────────────────
FONT_MAIN = "Times New Roman"
FONT_SIZE_MAIN = Pt(14)           # 14 пт
LINE_SPACING_MAIN = 1.5           # Полуторный
LINE_SPACING_SINGLE = 1           # Одинарный (таблицы, рисунки)
FIRST_LINE_INDENT = Cm(1.25)      # Отступ первой строки — 1,25 см


# ─── Заголовки (Таблица 2.1) ────────────────────────────────────────────────
# Заголовок 1-го уровня: 18 пт, полужирный, все прописные, с новой страницы
HEADING1_FONT_SIZE = Pt(18)
HEADING1_SPACE_BEFORE = Pt(0)
HEADING1_SPACE_AFTER = Pt(12)

# Заголовок 2-го уровня: 16 пт, полужирный
HEADING2_FONT_SIZE = Pt(16)
HEADING2_SPACE_BEFORE = Pt(24)
HEADING2_SPACE_AFTER = Pt(12)

# Заголовок 3+ уровня: 14 пт, полужирный
HEADING3_FONT_SIZE = Pt(14)
HEADING3_SPACE_BEFORE = Pt(24)
HEADING3_SPACE_AFTER = Pt(12)


# ─── Подписи / Captions ─────────────────────────────────────────────────────
CAPTION_FONT_SIZE = Pt(12)
CAPTION_SEPARATOR = " \u2014 "    # " — " (em dash), ГОСТ: через тире

# Интервалы подписей (ГОСТ Таблицы 6.1, 7.1, 8.1)
# Таблица: перед=6пт после=0; Рисунок: перед=0 после=6пт; Листинг: перед=6пт после=0
CAPTION_SPACE_BEFORE_TABLE   = Pt(6)
CAPTION_SPACE_BEFORE_IMAGE   = Pt(0)
CAPTION_SPACE_BEFORE_LISTING = Pt(6)
CAPTION_SPACE_AFTER_TABLE    = Pt(0)
CAPTION_SPACE_AFTER_IMAGE    = Pt(6)
CAPTION_SPACE_AFTER_LISTING  = Pt(0)


# ─── Таблицы (Таблица 6.1, п. 6) ───────────────────────────────────────────
TABLE_CONTENT_FONT_SIZE = Pt(12)
TABLE_CELL_OFFSET = Pt(10)        # Компенсация внутренних padding ячеек
TABLE_BORDER_HEIGHT = Pt(0.5)     # Высота одной горизонтальной линии таблицы
TABLE_CAPTION_CATEGORY = "Таблица"
TABLE_CONTINUATION_PREFIX = "Продолжение Таблицы"  # ГОСТ п. 6.3 — с большой «Т»


# ─── Рисунки (Таблица 7.1, п. 7) ───────────────────────────────────────────
IMAGE_CAPTION_CATEGORY = "Рисунок"
IMAGE_RESIZE_THRESHOLD = 0.7      # Порог сжатия: если 70% картинки влезает, уменьшаем


# ─── Формулы (раздел 5) ─────────────────────────────────────────────────────
EQUATION_CAPTION_CATEGORY = "Формула"
EQUATION_DEFAULT_HEIGHT = Pt(50)   # TODO: рассчитывать высоту формулы динамически
EQUATION_NUMBER_CELL_WIDTH = Pt(30)


# ─── Листинги (Таблица 8.1, п. 8) ──────────────────────────────────────────
FONT_CODE = "Courier New"
FONT_SIZE_CODE = Pt(10)           # ГОСТ: 10 пт  (в Template.docx: 12 пт!)
LISTING_CAPTION_CATEGORY = "Листинг"
LISTING_CONTINUATION_PREFIX = "Продолжение Листинга"  # С большой «Л»
LISTING_OFFSET = Pt(14)           # Компенсация внутренних padding рамки листинга
LISTING_BORDER_HEIGHT = Pt(1)     # Суммарная высота верхней и нижней границ рамки
LISTING_PYGMENTS_STYLE = "sas"    # Pygments colour scheme для подсветки синтаксиса


# ─── Списки (Таблица 4.1, п. 4) ────────────────────────────────────────────
LIST_MARKER_UNORDERED = "●"       # Допустимые по ГОСТ: «--», «―», «●», «■», «○»
LIST_MARKER_INDENT = Cm(1.0)      # Расстояние от маркера до текста (ГОСТ: текст на 2.25, маркер на 1.25)
LIST_LEVEL_INDENT = Cm(1.0)       # Дополнительный отступ на каждый уровень вложенности
LIST_TAB_STOP = Cm(1.0)           # Табуляция от начала абзаца до текста


# ─── Содержание (TOC) ──────────────────────────────────────────────────────
TOC_ENTRY_SPACE_AFTER = Cm(0.18)
TOC_LEVEL_INDENT = "    "          # 4 пробела — визуальный отступ на уровень вложенности TOC


# ─── Интервалы после таблиц/caption (п. 6.6, и код) ────────────────────────
SPACE_AFTER_TABLE = Cm(0.35)      # Перед абзацем, следующим за таблицей
SPACE_BEFORE_CAPTION_AFTER_TABLE = Cm(0.45)  # Перед caption, идущим после таблицы


# ─── Orphan / widow control ─────────────────────────────────────────────────
ORPHAN_CONTROL_LINES = 3          # heading/caption: page-break если < N строк влезает после


# ─── ParagraphSizer: хардкоженные line_height ───────────────────────────────
# Эмпирические значения, потому что FreeType не даёт точного line_height для docx.
LINE_HEIGHT_TIMES_14 = Pt(16.05)
LINE_HEIGHT_COURIER_12 = Pt(13.61)
SPACE_WIDTH_CORRECTION = 0.81     # Эмпирический множитель ширины пробела (non-mono)


# ─── PageBreak ──────────────────────────────────────────────────────────────
PAGE_BREAK_FONT_SIZE = Pt(1)      # Размер шрифта для невидимого абзаца PageBreak


# ─── Имена стилей в Template.docx ──────────────────────────────────────────
# Весь код обращается к стилям по строковым именам — собраны здесь для единообразия.
STYLE_NORMAL = "Normal"
STYLE_HEADING_PREFIX = "Heading"   # "Heading 1", "Heading 2", ...
STYLE_CAPTION = "Caption"
STYLE_CODE = "Code"
STYLE_TABLE_GRID = "Table Grid"
STYLE_NORMAL_TABLE = "Normal Table"
STYLE_FORMULA_CONTENT = "Formula Content"
STYLE_FORMULA_NUMBERING = "Formula Numbering"
STYLE_HYPERLINK = "Hyperlink"
