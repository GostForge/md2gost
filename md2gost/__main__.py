#!/bin/python
from argparse import ArgumentParser, BooleanOptionalAction
import os.path
from getpass import getuser
from pathlib import Path

from .config import load_project_config
from .converter import Converter


_PROJECT_CONFIG_FILENAMES = ("gostforge.yml", "gostforge.yaml")
_DOCX_SUFFIX = ".docx"
_MARKDOWN_SUFFIX = ".md"


def _discover_project_config_path(explicit_path: str | None, filenames: list[str]) -> Path | None:
    if explicit_path:
        return Path(explicit_path).expanduser()

    cwd = Path.cwd()
    for candidate_name in _PROJECT_CONFIG_FILENAMES:
        candidate = cwd / candidate_name
        if candidate.is_file():
            return candidate

    if not filenames:
        return None

    first_input = Path(filenames[0]).expanduser()
    if not first_input.is_absolute():
        first_input = (cwd / first_input).resolve()

    for parent in (first_input.parent, *first_input.parent.parents):
        for candidate_name in _PROJECT_CONFIG_FILENAMES:
            candidate = parent / candidate_name
            if candidate.is_file():
                return candidate

    return None


def _validate_input_files(filenames: list[str]) -> int | None:
    if not filenames:
        print("Нет входных файлов!")
        return -1

    if not all(fn.lower().endswith(_MARKDOWN_SUFFIX) for fn in filenames):
        print("Ошибка: файл должен иметь расширение .md")
        return 1

    return None


def _validate_docx_path(path: str | None, message: str) -> int | None:
    if path and not path.lower().endswith(_DOCX_SUFFIX):
        print(message)
        return -2
    return None


def _load_runtime_config(args, filenames: list[str]):
    config_path = _discover_project_config_path(args.config, filenames)
    try:
        config = load_project_config(config_path, allow_missing=args.config is None)
    except (OSError, ValueError) as exc:
        print(f"Ошибка загрузки конфигурации: {exc}")
        return None

    if args.syntax_highlighting is not None:
        config.syntax_highlighting = args.syntax_highlighting

    if config.title_pages < 1:
        print("Ошибка: title_pages должен быть >= 1")
        return None

    return config


def main():
    parser = ArgumentParser(
        prog="md2gost",
        description="Этот скрипт предназначен для генерирования отчетов/\
                курсовых работ по ГОСТ в формате docx из Markdown-файла."
    )
    parser.add_argument("filenames", nargs="*",
                        help="Путь до исходного(-ых) markdown файла(-ов)")
    parser.add_argument("-o", "--output", help="Путь до сгенерированного \
                            файла")
    parser.add_argument("-t", "--template", help="Путь до шаблона .docx")
    parser.add_argument("-T", "--title", help="Путь до файла титульной(-ых) \
                            страниц(ы) в формете docx")
    parser.add_argument("-c", "--config", help="Путь до gostforge.yml")
    parser.add_argument("--syntax-highlighting", help="Подсветка синтаксиса в листингах",
                        action=BooleanOptionalAction)
    parser.add_argument("--debug", help="Добавляет отладочные данные в документ",
                        action="store_true")

    args = parser.parse_args()
    filenames, output, template, title = args.filenames, args.output, args.template, args.title

    input_error = _validate_input_files(filenames)
    if input_error is not None:
        return input_error

    config = _load_runtime_config(args, filenames)
    if config is None:
        return -2

    template_error = _validate_docx_path(template, "Ошибка: шаблон должен иметь расширение .docx")
    if template_error is not None:
        return template_error

    title_error = _validate_docx_path(title, "Ошибка: титульник должен иметь расширение .docx")
    if title_error is not None:
        return title_error

    if output:
        if not output.lower().endswith(_DOCX_SUFFIX):
            print("Ошибка: выходной файл должен иметь расширение .docx")
            exit(2)
    else:
        output = f"{Path(filenames[0]).stem}{_DOCX_SUFFIX}"

    if not template:
        template = os.path.join(os.path.dirname(__file__), "Template.docx")

    debug_mode = args.debug or config.debug

    converter = Converter(
        input_paths=filenames,
        output_path=output,
        template_path=template,
        title_path=title,
        title_pages=config.title_pages,
        debug=debug_mode,
        config=config,
    )
    converter.convert()

    document = converter.document

    document.core_properties.author = getuser()
    document.core_properties.comments =\
        "Создано при помощи https://github.com/witelokk/md2gost"

    document.save(output)
    print(f"Сгенерированный документ: {os.path.abspath(output)}")

    if debug_mode:
        import platform
        if platform.system() == 'Darwin':       # macOS
            import subprocess
            subprocess.call(('open', output))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(output)
        else:                                   # linux variants
            import subprocess
            subprocess.call(('xdg-open', output))


if __name__ == "__main__":
    main()
