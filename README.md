# md2gost

Скрипт для генерации отчёта в формате DOCX по ГОСТ из Markdown-файла.

[Roadmap проекта](https://swift-turquoise-639.notion.site/c28b6a70173c4a35ace9385c25225bb6?v=fa46ce943a1d4f13bf574d665a0b0111&pvs=4)

## HTTP-сервер (интеграция с GostForge)

В `md2gost` встроен FastAPI HTTP-сервер для интеграции с backend GostForge.

### Запуск сервера

```bash
# Через entry point
md2gost-server

# Либо напрямую
python -m md2gost.server

# Через Docker
docker build -t md2gost .
docker run -p 8000:8000 md2gost
```

### API endpoints

| Endpoint | Метод | Описание |
|---|---|---|
| `/health` | GET | Проверка доступности сервиса |
| `/convert` | POST | Синхронная конвертация Markdown → DOCX |
| `/jobs` | POST | Создание асинхронной задачи (ответ 202) |
| `/jobs/{id}` | GET | Получение статуса задачи |
| `/jobs/{id}/result` | GET | Скачивание результата завершённой задачи |

### Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `MD2GOST_HOST` | `0.0.0.0` | Хост, на котором слушает сервер |
| `MD2GOST_PORT` | `8000` | Порт сервера |

### Поддержка callback URL

При создании асинхронной задачи через `POST /jobs` можно передать поле формы `callback_url`.
После завершения задачи (или ошибки) сервер выполнит POST c JSON-статусом на указанный URL.

---

## Основные возможности

- Генерация отчёта;
- Добавление титульной страницы в формате DOCX;
- Генерация интерактивного содержания;
- Поддержка сквозной нумерации и кросс-референсов;
- Автоматическая нумерация рисунков, продолжений таблиц, листингов и т.д.

## Пример

Markdown-файл: [example.md](https://github.com/witelokk/md2gost/blob/main/examples/example.md)

Сгенерированный файл в ZIP-архиве (команда `python -m md2gost --syntax-highlighting example.md`): [example.zip](https://nightly.link/witelokk/md2gost/workflows/example-generator/main/example.zip?h=f65c99d31a9379f44fcc6e923de4a735a271d5aa)

## Установка

```bash
pip install --upgrade git+https://github.com/witelokk/md2gost.git@main
```

Если ваша система использует стандарт [PEP 668](https://peps.python.org/pep-0668/), рекомендуется [pipx](https://pypa.github.io/pipx/):

```bash
pipx install git+https://github.com/witelokk/md2gost.git@main
```

## Использование

```text
(python -m ) md2gost [-h] [-o OUTPUT] [-T TITLE] [--title-pages TITLE_PAGES] [--syntax-highlighting | --no-syntax-highlighting] [--debug] [filenames ...]
```

Если флаг `-o` не указан, итоговый отчёт создаётся с именем исходного файла и расширением `.docx`.

## Фичи

### Добавление титульной страницы

Чтобы добавить титульную страницу, используйте флаг `--title` (`-T`) с путём к DOCX-файлу титульника.
Если в документе больше одной страницы, укажите количество через `--title-pages`.

Пример:

```bash
md2gost report.md --title title.docx --title-pages 2
```

### Подписи рисунков, листингов, таблиц

Рисунки:

```markdown
![](path/to/image "%unique_name Текст подписи")
```

Таблицы:

```markdown
%uniquename Текст подписи

| a | b | c |
|---|---|---|
| a | b | c |
```

Листинги:

~~~markdown
%uniquename Текст подписи

```python
print("hello world")
```
~~~

Формулы:

```markdown
%uniquename

$$
2 + 2 = 4
$$
```

`uniquename` — уникальное имя для кросс-ссылок.

### Ссылки

Чтобы вставить кликабельный номер рисунка/листинга/таблицы, используйте:

```markdown
Рис. @unique_name
```

### Заголовки основных разделов без нумерации

Чтобы заголовок был без сквозной нумерации (например, «СОДЕРЖАНИЕ»), используйте:

```markdown
# *СОДЕРЖАНИЕ
```

### Генерация содержания

```markdown
[TOC]
```

### Подсветка синтаксиса в листингах

Используйте флаг `--syntax-highlighting`.

### Импорт кода в листингах

~~~markdown
```python code.py
```
~~~

где `code.py` — путь к файлу с исходным кодом.
