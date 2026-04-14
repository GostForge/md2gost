# Руководство по отладке md2gost

## 1. Встроенный `--debug` режим

md2gost уже имеет встроенный debugger (`debugger.py`), который добавляет визуальную
разметку прямо в выходной docx-файл — цветные прямоугольники показывают рассчитанные
высоты элементов.

```bash
# Запуск с отладочной визуализацией
cd md2gost
python -m md2gost example.md --debug
# Файл откроется автоматически (xdg-open на Linux)
```

Что показывает `--debug`:
- Зелёные полосы — рассчитанная высота каждого элемента
- Помогает увидеть, где layout_tracker ошибается в расчёте переносов на следующую страницу


## 2. Исследование Template.docx

Template.docx — это docx-файл-шаблон, содержащий **только стили** (без текста).
md2gost загружает его и генерирует контент, наследуя стили.

### Что внутри Template.docx

```python
# Скрипт для инспекции шаблона
import docx

doc = docx.Document("md2gost/md2gost/Template.docx")

# Поля страницы
s = doc.sections[0]
print(f"Поля: лево={s.left_margin/360000:.2f}cm, право={s.right_margin/360000:.2f}cm")
print(f"       верх={s.top_margin/360000:.2f}cm, низ={s.bottom_margin/360000:.2f}cm")

# Стили
for style in doc.styles:
    if hasattr(style, 'font') and style.font and style.font.name:
        pf = style.paragraph_format if hasattr(style, 'paragraph_format') else None
        print(f"{style.name}: font={style.font.name}, size={style.font.size}, "
              f"bold={style.font.bold}, italic={style.font.italic}")
        if pf:
            print(f"  alignment={pf.alignment}, first_indent={pf.first_line_indent}, "
                  f"space_before={pf.space_before}, space_after={pf.space_after}, "
                  f"line_spacing={pf.line_spacing}")
```

### Ключевые стили в Template.docx

| Стиль | Шрифт | Размер | Начертание | Используется для |
|-------|-------|--------|------------|-----------------|
| Normal | Times New Roman | 14 пт | Обычный | Основной текст |
| Heading 1 | (inherited) | (inherited) | Bold | Разделы (# ) |
| Heading 2 | (inherited) | (inherited) | Bold | Подразделы (## ) |
| Heading 3-9 | (inherited) | (inherited) | Bold | Пункты (### +) |
| Caption | (inherited) | (inherited) | Italic | Подписи таблиц/рисунков/листингов |
| Code | Courier New | 12 пт | Обычный | Содержание листингов |
| Formula Content | (inherited) | (inherited) | — | Левая ячейка формулы (центр) |
| Formula Numbering | (inherited) | (inherited) | — | Правая ячейка формулы (номер) |
| Table Text | (inherited) | (inherited) | — | Текст внутри таблиц |
| Hyperlink | — | — | Синий, подчёркнутый | Ссылки |

**Важно:**
- Heading 1 НЕ имеет собственного `font.size` — наследует 14 пт от Normal!
  По ГОСТ должен быть 18 пт. Размер задаётся через numbering XML.
- Caption — italic, без bold. По ГОСТ подпись рисунка = bold, подпись таблицы = italic.
  Сейчас один стиль для всех.


## 3. Пошаговая отладка pipeline

Конвейер обработки в `converter.py`:

```
Parser.parse(markdown_text)
    └─→ список Renderable-объектов
         │
    TocPreProcessor.process(renderables)    # Заполняет TOC заголовками
         │
    NumberingPreProcessor.process(renderables)  # Нумерует таблицы/рисунки/листинги
         │
    Renderer.process(renderables)           # Генерирует docx-элементы
         │
    TocPostProcessor.process(renderables)   # Проставляет номера страниц в TOC
```

### Отладка парсера

```python
from md2gost.extended_markdown import markdown

text = """
# Введение
Текст абзаца.

## Подраздел

| A | B |
|---|---|
| 1 | 2 |
"""

parsed = markdown.parse(text)
for elem in parsed.children:
    print(type(elem).__name__, getattr(elem, 'level', ''), getattr(elem, 'numbered', ''))
```

### Отладка Renderable-объектов

```python
import docx
from md2gost.parser_ import Parser

doc = docx.Document("md2gost/md2gost/Template.docx")
parser = Parser(doc)
parser.parse("# Заголовок\n\nТекст\n", "/tmp")

for r in parser.get_rendered():
    print(type(r).__name__, getattr(r, '_level', ''), getattr(r, 'text', '')[:50])
```

### Отладка нумерации

```python
from md2gost.numberer import NumberingPreProcessor

renderables = parser.get_rendered()
numberer = NumberingPreProcessor()
numberer.process(renderables)
print(numberer._categories)        # {'Таблица': 1, 'Рисунок': 2, ...}
print(numberer._reference_data)    # {'goods': 1, 'listing': 1, ...}
```

### Отладка layout-трекинга

```python
from md2gost.layout_tracker import LayoutTracker
from docx.shared import Cm, Mm

tracker = LayoutTracker(max_height=Mm(253), max_width=Mm(165))
print(f"Page {tracker.current_state.page}, "
      f"remaining={tracker.current_state.remaining_page_height/36000:.1f}mm")

# Симуляция: добавляем элемент высотой 200 мм
tracker.add_height(Mm(200))
print(f"Page {tracker.current_state.page}, "
      f"remaining={tracker.current_state.remaining_page_height/36000:.1f}mm")
```


## 4. Отладка конкретных проблем

### Проблема: элемент не на той странице

1. Запустите с `--debug`, найдите элемент визуально.
2. Поставьте breakpoint в `render()` нужного Renderable-класса.
3. Проверьте `layout_state.remaining_page_height` — сколько места осталось на странице.
4. Проверьте `height_data` из `ParagraphSizer.calculate_height()` — правильно ли рассчитана высота.

### Проблема: шрифт не тот

1. Проверьте стиль элемента: какой `style` назначен.
2. Проверьте цепочку наследования: стиль → base_style → ... → Normal → docDefaults.
3. `merge_objects()` сливает атрибуты в порядке приоритета, ближайший non-None побеждает.

### Проблема: ParagraphSizer считает неправильно

Самое хрупкое место. Причины:
- **Шрифт не найден** — `find_font.py` фолбэчит на другой шрифт (см. WARNING в логах).
- **Хардкоженные line_height** — `Pt(16.05)` для Times 14, `Pt(13.61)` для Courier 12.
- **Ширина текста** — `Font.get_text_width()` использует Pillow, результат может отличаться.

```bash
# Проверка, какой шрифт реально используется
python3 -c "from md2gost.renderable.find_font import find_font; print(find_font('Times New Roman', False, False))"
```


## 5. Полезные команды

```bash
# Запуск тестов
cd md2gost
python -m pytest tests/ -v

# Конвертация с подсветкой синтаксиса
python -m md2gost input.md --syntax-highlighting -o output.docx

# Конвертация с титульной страницей
python -m md2gost input.md -T title.docx -o output.docx

# Инспекция выходного docx
python3 -c "
import docx
doc = docx.Document('output.docx')
for i, p in enumerate(doc.paragraphs[:20]):
    print(f'{i}: style={p.style.name} text={p.text[:60]!r}')
"

# Включить подробное логирование
PYTHONPATH=. python -c "
import logging; logging.basicConfig(level=logging.DEBUG)
from md2gost.converter import Converter
c = Converter(['example.md'], 'out.docx')
c.convert()
c.document.save('out.docx')
"
```
