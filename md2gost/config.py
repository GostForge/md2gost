"""
Конфигурация md2gost — параметры, которые пользователь может менять.

Все значения по умолчанию соответствуют ГОСТ. Переопределить можно через:
  1. Аргументы конструктора Md2GostConfig(...)
  2. (Будущее) YAML/JSON конфиг-файл
  3. (Будущее) CLI-аргументы
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from enum import IntFlag, auto
from pathlib import Path
from typing import Any, Mapping

import yaml
from docx.shared import Cm, Inches, Length, Mm, Pt, Twips


class CaptionTextStyle(IntFlag):
    """Bit flags for caption text decoration."""

    NONE = 0
    BOLD = auto()
    ITALIC = auto()
    UNDERLINE = auto()


def docs(description: str, *, default: Any):
    """Attach human-readable documentation to a config field."""
    return field(default=default, metadata={"doc": description})


@dataclass
class Md2GostConfig:
    """Конфигурационный объект md2gost.

    Позволяет переопределять параметры, не трогая ни Template.docx, ни код.
    Все значения по умолчанию === ГОСТ.
    """

    # ── Поля страницы ────────────────────────────────────────────────────
    page_width_a4: Length = docs("Ширина страницы А4", default=Mm(210))
    page_height_a4: Length = docs("Высота страницы А4", default=Mm(297))
    page_margin_left: Length = docs("Левое поле страницы", default=Cm(3.0))
    page_margin_right: Length = docs("Правое поле страницы", default=Cm(1.0))
    page_margin_top: Length = docs("Верхнее поле страницы", default=Cm(2.0))
    page_margin_bottom: Length = docs("Нижнее поле страницы", default=Cm(2.0))
    bottom_margin_effective: Length = docs(
        "Эффективное нижнее поле для расчёта рабочей высоты",
        default=Cm(1.86),
    )

    # ── Основной текст ──────────────────────────────────────────────────
    font_main: str = docs("Основной шрифт документа", default="Times New Roman")
    font_size_main: Length = docs("Размер основного шрифта", default=Pt(14))
    line_spacing: float = docs("Межстрочный интервал основного текста", default=1.5)
    line_spacing_single: float = docs("Одинарный межстрочный интервал", default=1.0)
    first_line_indent: Length = docs("Красная строка основного текста", default=Cm(1.25))

    # ── Заголовки ────────────────────────────────────────────────────────
    heading1_font_size: Length = docs("Размер заголовка 1 уровня", default=Pt(18))
    heading1_space_before: Length = docs("Интервал перед заголовком 1 уровня", default=Pt(0))
    heading1_space_after: Length = docs("Интервал после заголовка 1 уровня", default=Pt(12))
    heading2_font_size: Length = docs("Размер заголовка 2 уровня", default=Pt(16))
    heading2_space_before: Length = docs("Интервал перед заголовком 2 уровня", default=Pt(24))
    heading2_space_after: Length = docs("Интервал после заголовка 2 уровня", default=Pt(12))
    heading3_font_size: Length = docs("Размер заголовка 3+ уровня", default=Pt(14))
    heading3_space_before: Length = docs("Интервал перед заголовком 3+ уровня", default=Pt(24))
    heading3_space_after: Length = docs("Интервал после заголовка 3+ уровня", default=Pt(12))

    # ── Листинги ────────────────────────────────────────────────────────
    font_code: str = docs("Шрифт кода в листингах", default="Courier New")
    font_size_code: Length = docs("Размер шрифта кода в листингах", default=Pt(10))
    syntax_highlighting: bool = docs("Включить подсветку синтаксиса листингов", default=False)
    listing_offset: Length = docs("Компенсация внутреннего padding рамки листинга", default=Pt(14))
    listing_border_height: Length = docs("Суммарная высота границ листинга", default=Pt(1))
    listing_pygments_style: str = docs("Цветовая схема подсветки Pygments", default="sas")

    # ── Списки ──────────────────────────────────────────────────────────
    list_marker: str = docs("Маркер маркированного списка", default="●")
    list_marker_indent: Length = docs("Отступ маркера списка", default=Cm(1.0))
    list_level_indent: Length = docs("Дополнительный отступ на уровень списка", default=Cm(1.0))
    list_tab_stop: Length = docs("Позиция tab-stop после маркера", default=Cm(1.0))

    # ── Captions ────────────────────────────────────────────────────────
    caption_font_size: Length = docs("Базовый размер шрифта подписи", default=Pt(12))
    caption_separator: str = docs("Разделитель номера и текста подписи", default=" \u2014 ")
    # Категории можно переименовать (например, «Рис.» вместо «Рисунок»)
    caption_table: str = docs("Категория подписей таблиц", default="Таблица")
    caption_image: str = docs("Категория подписей рисунков", default="Рисунок")
    caption_listing: str = docs("Категория подписей листингов", default="Листинг")
    caption_equation: str = docs("Категория подписей формул", default="Формула")
    # Оформление подписей через bit flags (можно комбинировать через |)
    caption_table_style: CaptionTextStyle = docs(
        "Стиль подписи таблиц (bold|italic|underline)",
        default=CaptionTextStyle.ITALIC,
    )
    caption_image_style: CaptionTextStyle = docs(
        "Стиль подписи рисунков (bold|italic|underline)",
        default=CaptionTextStyle.BOLD,
    )
    caption_listing_style: CaptionTextStyle = docs(
        "Стиль подписи листингов (bold|italic|underline)",
        default=CaptionTextStyle.ITALIC,
    )
    caption_equation_style: CaptionTextStyle = docs(
        "Стиль подписи формул (bold|italic|underline)",
        default=CaptionTextStyle.NONE,
    )
    caption_table_space_before: Length = docs("Интервал перед подписью таблицы", default=Pt(6))
    caption_table_space_after: Length = docs("Интервал после подписи таблицы", default=Pt(0))
    caption_image_space_before: Length = docs("Интервал перед подписью рисунка", default=Pt(0))
    caption_image_space_after: Length = docs("Интервал после подписи рисунка", default=Pt(6))
    caption_listing_space_before: Length = docs("Интервал перед подписью листинга", default=Pt(6))
    caption_listing_space_after: Length = docs("Интервал после подписи листинга", default=Pt(0))

    # ── Продолжения при переносе ────────────────────────────────────────
    table_continuation: str = docs("Префикс для продолжения таблицы", default="Продолжение Таблицы")
    listing_continuation: str = docs("Префикс для продолжения листинга", default="Продолжение Листинга")

    # ── Таблицы ─────────────────────────────────────────────────────────
    table_content_font_size: Length = docs("Размер шрифта текста внутри таблицы", default=Pt(12))
    table_cell_offset: Length = docs("Компенсация внутреннего padding ячейки", default=Pt(10))
    table_border_height: Length = docs("Высота одной горизонтальной границы таблицы", default=Pt(0.5))
    space_after_table: Length = docs("Интервал перед абзацем после таблицы", default=Cm(0.35))
    space_before_caption_after_table: Length = docs(
        "Интервал перед подписью после таблицы",
        default=Cm(0.45),
    )

    # ── Рисунки ─────────────────────────────────────────────────────────
    image_resize_threshold: float = docs("Порог сжатия изображения при нехватке места", default=0.7)

    # ── Формулы ─────────────────────────────────────────────────────────
    equation_height: Length = docs("Базовая высота строки формулы", default=Pt(50))
    equation_number_width: Length = docs("Ширина ячейки номера формулы", default=Pt(30))

    # ── TOC ─────────────────────────────────────────────────────────────
    toc_entry_space_after: Length = docs("Интервал после строки в содержании", default=Cm(0.18))
    toc_level_indent: str = docs("Отступ на уровень вложенности TOC", default="    ")

    # ── Эвристики layout ────────────────────────────────────────────────
    orphan_control_lines: int = docs(
        "Минимум строк после заголовка/подписи до переноса страницы",
        default=3,
    )
    line_height_times_14: Length = docs(
        "Эмпирическая высота строки Times New Roman 14",
        default=Pt(16.05),
    )
    line_height_courier_12: Length = docs(
        "Эмпирическая высота строки Courier New 12",
        default=Pt(13.61),
    )
    space_width_correction: float = docs(
        "Поправка ширины пробела для non-mono шрифтов",
        default=0.81,
    )
    page_break_font_size: Length = docs(
        "Технический размер шрифта для невидимого page-break абзаца",
        default=Pt(1),
    )

    # ── Style names in Template.docx ────────────────────────────────────
    style_normal: str = docs("Стиль основного абзаца", default="Normal")
    style_heading_prefix: str = docs("Префикс стилей заголовков", default="Heading")
    style_caption: str = docs("Стиль подписи", default="Caption")
    style_code: str = docs("Стиль абзаца кода", default="Code")
    style_table_grid: str = docs("Табличный стиль по умолчанию", default="Table Grid")
    style_normal_table: str = docs("Базовый стиль таблицы", default="Normal Table")
    style_formula_content: str = docs("Стиль левой ячейки формулы", default="Formula Content")
    style_formula_numbering: str = docs("Стиль правой ячейки формулы", default="Formula Numbering")
    style_hyperlink: str = docs("Стиль гиперссылки", default="Hyperlink")

    # ── Нумерация ───────────────────────────────────────────────────────
    # True = посекционная нумерация (Рисунок 2.3), False = сквозная (Рисунок 3)
    sectional_numbering: bool = docs(
        "Включить посекционную нумерацию (Рисунок 2.3)",
        default=False,
    )  # В текущей версии по умолчанию используется сквозная нумерация

    # ── Титульная страница ──────────────────────────────────────────────
    title_pages: int = docs("Количество страниц титульника", default=1)

    # ── Отладка ─────────────────────────────────────────────────────────
    debug: bool = docs("Включить отладочный режим генерации", default=False)


_LENGTH_RE = re.compile(
    r"^\s*(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>pt|cm|mm|in|inch|inches|twip|twips)?\s*$",
    re.IGNORECASE,
)

_CONFIG_ROOT_KEY = "md2gost"
_CONFIG_GENERATOR_KEY = "generator"

_FIELD_NAMES = {field.name for field in fields(Md2GostConfig)}
_FIELD_ALIASES = {
    "title-pages": "title_pages",
    "page-width-a4": "page_width_a4",
    "page-height-a4": "page_height_a4",
    "font-main": "font_main",
    "font-size-main": "font_size_main",
    "font-size-code": "font_size_code",
    "line-spacing": "line_spacing",
    "first-line-indent": "first_line_indent",
    "list-marker": "list_marker",
    "list-marker-indent": "list_marker_indent",
    "list-level-indent": "list_level_indent",
    "caption-separator": "caption_separator",
    "table-continuation": "table_continuation",
    "listing-continuation": "listing_continuation",
    "equation-height": "equation_height",
    "equation-number-width": "equation_number_width",
    "sectional-numbering": "sectional_numbering",
    "syntax-highlighting": "syntax_highlighting",
    "page-margin-left": "page_margin_left",
    "page-margin-right": "page_margin_right",
    "page-margin-top": "page_margin_top",
    "page-margin-bottom": "page_margin_bottom",
}

_LENGTH_FIELDS = {
    "page_width_a4",
    "page_height_a4",
    "page_margin_left",
    "page_margin_right",
    "page_margin_top",
    "page_margin_bottom",
    "bottom_margin_effective",
    "font_size_main",
    "first_line_indent",
    "heading1_font_size",
    "heading1_space_before",
    "heading1_space_after",
    "heading2_font_size",
    "heading2_space_before",
    "heading2_space_after",
    "heading3_font_size",
    "heading3_space_before",
    "heading3_space_after",
    "caption_font_size",
    "caption_table_space_before",
    "caption_table_space_after",
    "caption_image_space_before",
    "caption_image_space_after",
    "caption_listing_space_before",
    "caption_listing_space_after",
    "table_content_font_size",
    "table_cell_offset",
    "table_border_height",
    "space_after_table",
    "space_before_caption_after_table",
    "font_size_code",
    "listing_offset",
    "listing_border_height",
    "list_marker_indent",
    "list_level_indent",
    "list_tab_stop",
    "equation_height",
    "equation_number_width",
    "toc_entry_space_after",
    "line_height_times_14",
    "line_height_courier_12",
    "page_break_font_size",
}

_BOOLEAN_FIELDS = {
    "syntax_highlighting",
    "sectional_numbering",
    "debug",
}

_INT_FIELDS = {
    "title_pages",
    "orphan_control_lines",
}

_FLOAT_FIELDS = {
    "line_spacing",
    "line_spacing_single",
    "image_resize_threshold",
    "space_width_correction",
}

_STRING_FIELDS = {
    "font_main",
    "font_code",
    "list_marker",
    "caption_separator",
    "caption_table",
    "caption_image",
    "caption_listing",
    "caption_equation",
    "table_continuation",
    "listing_continuation",
    "listing_pygments_style",
    "toc_level_indent",
    "style_normal",
    "style_heading_prefix",
    "style_caption",
    "style_code",
    "style_table_grid",
    "style_normal_table",
    "style_formula_content",
    "style_formula_numbering",
    "style_hyperlink",
}

_CAPTION_STYLE_FIELDS = {
    "caption_table_style",
    "caption_image_style",
    "caption_listing_style",
    "caption_equation_style",
}

_CAPTION_STYLE_FLAGS: dict[str, CaptionTextStyle] = {
    "bold": CaptionTextStyle.BOLD,
    "italic": CaptionTextStyle.ITALIC,
    "underline": CaptionTextStyle.UNDERLINE,
}


def _normalize_field_name(raw_name: str) -> str:
    raw = raw_name.strip()
    raw_lower = raw.lower()
    normalized = raw_lower.replace("-", "_").replace(".", "_")
    return _FIELD_ALIASES.get(raw, _FIELD_ALIASES.get(raw_lower, normalized))


def _parse_bool(raw_value: Any, field_name: str) -> bool:
    if isinstance(raw_value, bool):
        return raw_value

    if isinstance(raw_value, str):
        value = raw_value.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False

    raise ValueError(f"Поле '{field_name}' должно быть bool")


def _parse_int(raw_value: Any, field_name: str) -> int:
    if isinstance(raw_value, bool):
        raise ValueError(f"Поле '{field_name}' должно быть integer")

    if isinstance(raw_value, int):
        return raw_value

    if isinstance(raw_value, str):
        text = raw_value.strip()
        if text and (text.isdigit() or (text[0] == "-" and text[1:].isdigit())):
            return int(text)

    raise ValueError(f"Поле '{field_name}' должно быть integer")


def _parse_float(raw_value: Any, field_name: str) -> float:
    if isinstance(raw_value, bool):
        raise ValueError(f"Поле '{field_name}' должно быть number")

    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    if isinstance(raw_value, str):
        try:
            return float(raw_value.strip())
        except ValueError as exc:
            raise ValueError(f"Поле '{field_name}' должно быть number") from exc

    raise ValueError(f"Поле '{field_name}' должно быть number")


def _parse_length(raw_value: Any, field_name: str) -> Length:
    if isinstance(raw_value, Length):
        return raw_value

    if isinstance(raw_value, bool):
        raise ValueError(f"Поле '{field_name}' должно быть длиной в формате '<число><единица>'")

    if isinstance(raw_value, (int, float)):
        return Pt(float(raw_value))

    if isinstance(raw_value, Mapping):
        value = raw_value.get("value")
        unit = raw_value.get("unit", "pt")
        if value is None:
            raise ValueError(f"Поле '{field_name}' должно содержать ключ 'value'")
        raw_value = f"{value}{unit}"

    if not isinstance(raw_value, str):
        raise ValueError(f"Поле '{field_name}' должно быть строкой длины или числом")

    match = _LENGTH_RE.match(raw_value)
    if not match:
        raise ValueError(
            f"Поле '{field_name}' должно быть в формате '<число><единица>', например '12pt' или '2.5cm'"
        )

    value = float(match.group("value"))
    unit = (match.group("unit") or "pt").lower()

    if unit == "pt":
        return Pt(value)
    if unit == "cm":
        return Cm(value)
    if unit == "mm":
        return Mm(value)
    if unit in {"in", "inch", "inches"}:
        return Inches(value)
    if unit in {"twip", "twips"}:
        return Twips(int(round(value)))

    raise ValueError(f"Неподдерживаемая единица длины для '{field_name}': {unit}")


def _extract_caption_style_tokens(raw_value: Any, field_name: str) -> list[str]:
    if isinstance(raw_value, str):
        return [token for token in re.split(r"[|,\s]+", raw_value.strip().lower()) if token]

    if isinstance(raw_value, list):
        tokens: list[str] = []
        for item in raw_value:
            if not isinstance(item, str):
                raise ValueError(f"Поле '{field_name}' должно содержать строки со стилями")
            tokens.append(item.strip().lower())
        return tokens

    raise ValueError(f"Поле '{field_name}' должно быть строкой или списком")


def _apply_caption_style_token(
    current_style: CaptionTextStyle,
    token: str,
    field_name: str,
) -> CaptionTextStyle:
    if token in {"none", "normal"}:
        return CaptionTextStyle.NONE

    flag = _CAPTION_STYLE_FLAGS.get(token)
    if flag is None:
        raise ValueError(f"Поле '{field_name}' содержит неизвестный стиль '{token}'")

    return current_style | flag


def _parse_caption_style(raw_value: Any, field_name: str) -> CaptionTextStyle:
    if isinstance(raw_value, CaptionTextStyle):
        return raw_value

    if isinstance(raw_value, int) and not isinstance(raw_value, bool):
        try:
            return CaptionTextStyle(raw_value)
        except ValueError as exc:
            raise ValueError(f"Поле '{field_name}' содержит недопустимый флаг стиля") from exc

    tokens = _extract_caption_style_tokens(raw_value, field_name)

    if not tokens:
        return CaptionTextStyle.NONE

    style = CaptionTextStyle.NONE
    for token in tokens:
        style = _apply_caption_style_token(style, token, field_name)

    return style


def _extract_config_section(raw_config: Mapping[str, Any]) -> Mapping[str, Any]:
    section: Any = raw_config

    if _CONFIG_ROOT_KEY in raw_config:
        section = raw_config[_CONFIG_ROOT_KEY]
        if section is None:
            return {}
        if not isinstance(section, Mapping):
            raise ValueError(f"Секция '{_CONFIG_ROOT_KEY}' должна быть объектом")

    if isinstance(section, Mapping) and _CONFIG_GENERATOR_KEY in section:
        maybe_generator = section[_CONFIG_GENERATOR_KEY]
        if maybe_generator is None:
            return {}
        if not isinstance(maybe_generator, Mapping):
            raise ValueError(f"Секция '{_CONFIG_GENERATOR_KEY}' должна быть объектом")
        section = maybe_generator

    if not isinstance(section, Mapping):
        raise ValueError("Конфигурация gostforge.yml должна быть YAML-объектом")

    return section


def _convert_field_value(field_name: str, raw_value: Any) -> Any:
    if field_name in _CAPTION_STYLE_FIELDS:
        return _parse_caption_style(raw_value, field_name)
    if field_name in _LENGTH_FIELDS:
        return _parse_length(raw_value, field_name)
    if field_name in _BOOLEAN_FIELDS:
        return _parse_bool(raw_value, field_name)
    if field_name in _INT_FIELDS:
        return _parse_int(raw_value, field_name)
    if field_name in _FLOAT_FIELDS:
        return _parse_float(raw_value, field_name)
    if field_name in _STRING_FIELDS:
        if not isinstance(raw_value, str):
            raise ValueError(f"Поле '{field_name}' должно быть строкой")
        return raw_value

    if field_name in _FIELD_NAMES:
        return raw_value

    raise ValueError(f"Неизвестное поле конфигурации '{field_name}'")


def _ensure_positive_length(config: Md2GostConfig, field_name: str) -> None:
    value = getattr(config, field_name)
    if value.pt <= 0:
        raise ValueError(f"Параметр '{field_name}' должен быть > 0")


def _ensure_positive_number(config: Md2GostConfig, field_name: str) -> None:
    if getattr(config, field_name) <= 0:
        raise ValueError(f"Параметр '{field_name}' должен быть > 0")


def _ensure_non_empty_string(config: Md2GostConfig, field_name: str) -> None:
    if not str(getattr(config, field_name)).strip():
        raise ValueError(f"Параметр '{field_name}' не должен быть пустым")


def _validate_config(config: Md2GostConfig) -> None:
    _ensure_positive_length(config, "page_width_a4")
    _ensure_positive_length(config, "page_height_a4")
    _ensure_positive_length(config, "bottom_margin_effective")

    if config.title_pages < 1:
        raise ValueError("Параметр 'title_pages' должен быть >= 1")

    if config.orphan_control_lines < 0:
        raise ValueError("Параметр 'orphan_control_lines' должен быть >= 0")

    _ensure_positive_number(config, "line_spacing")
    _ensure_positive_number(config, "line_spacing_single")
    _ensure_positive_number(config, "space_width_correction")

    if config.image_resize_threshold <= 0 or config.image_resize_threshold > 1:
        raise ValueError("Параметр 'image_resize_threshold' должен быть в диапазоне (0, 1]")

    _ensure_non_empty_string(config, "font_main")
    _ensure_non_empty_string(config, "font_code")
    _ensure_non_empty_string(config, "list_marker")

    style_fields = (
        "style_normal",
        "style_heading_prefix",
        "style_caption",
        "style_code",
        "style_table_grid",
        "style_normal_table",
        "style_formula_content",
        "style_formula_numbering",
        "style_hyperlink",
    )
    for style_field in style_fields:
        _ensure_non_empty_string(config, style_field)


def build_config_from_mapping(raw_config: Mapping[str, Any]) -> Md2GostConfig:
    """Собирает Md2GostConfig из YAML-словаря с валидацией."""
    section = _extract_config_section(raw_config)
    overrides: dict[str, Any] = {}

    for raw_name, raw_value in section.items():
        if not isinstance(raw_name, str):
            raise ValueError("Ключи конфигурации должны быть строками")

        field_name = _normalize_field_name(raw_name)
        if field_name not in _FIELD_NAMES:
            raise ValueError(f"Неизвестный параметр md2gost: '{raw_name}'")

        if raw_value is None:
            continue

        overrides[field_name] = _convert_field_value(field_name, raw_value)

    config = Md2GostConfig(**overrides)
    _validate_config(config)
    return config


def load_config_from_yaml(config_path: str | Path) -> Md2GostConfig:
    """Загружает Md2GostConfig из файла gostforge.yml."""
    path = Path(config_path)

    with path.open("r", encoding="utf-8") as file_obj:
        parsed = yaml.safe_load(file_obj)

    if parsed is None:
        return Md2GostConfig()

    if not isinstance(parsed, Mapping):
        raise ValueError("Файл gostforge.yml должен содержать YAML-объект")

    return build_config_from_mapping(parsed)


def load_project_config(config_path: str | Path | None, *, allow_missing: bool = True) -> Md2GostConfig:
    """Загружает конфиг проекта, возвращая дефолт при отсутствии файла."""
    if config_path is None:
        return Md2GostConfig()

    path = Path(config_path)
    if not path.exists():
        if allow_missing:
            return Md2GostConfig()
        raise FileNotFoundError(f"Файл конфигурации не найден: {path}")

    return load_config_from_yaml(path)


def _serialize_reference_value(value: Any) -> Any:
    if isinstance(value, Length):
        return {
            "pt": round(float(value.pt), 4),
            "twips": int(value.twips),
        }

    if isinstance(value, CaptionTextStyle):
        if value == CaptionTextStyle.NONE:
            return ["none"]

        tokens: list[str] = []
        if value & CaptionTextStyle.BOLD:
            tokens.append("bold")
        if value & CaptionTextStyle.ITALIC:
            tokens.append("italic")
        if value & CaptionTextStyle.UNDERLINE:
            tokens.append("underline")
        return tokens

    return value


def get_config_reference() -> dict[str, dict[str, Any]]:
    """Возвращает эталонные значения и описание полей для клиента."""
    defaults = Md2GostConfig()
    reference: dict[str, dict[str, Any]] = {}

    for config_field in fields(Md2GostConfig):
        raw_value = getattr(defaults, config_field.name)
        reference[config_field.name] = {
            "doc": config_field.metadata.get("doc", ""),
            "default": _serialize_reference_value(raw_value),
        }

    return reference


# Синглтон по умолчанию — используется, если config не передан явно
_default_config: Md2GostConfig | None = None


def get_default_config() -> Md2GostConfig:
    """Вернуть глобальный конфиг (создаёт при первом вызове)."""
    global _default_config
    if _default_config is None:
        _default_config = Md2GostConfig()
    return _default_config


def set_default_config(config: Md2GostConfig | None) -> None:
    """Установить глобальный конфиг (полезно для тестов и сервера)."""
    global _default_config
    _default_config = config
