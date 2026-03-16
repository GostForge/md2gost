import logging
from collections import defaultdict

from .renderable import Renderable, Paragraph
from .renderable.heading import Heading
from .renderable.requires_numbering import RequiresNumbering


class NumberingPreProcessor:
    """Присваивает номера таблицам, рисункам, формулам, листингам.

    Поддерживает два режима:
    - **Сквозная** нумерация (sectional=False): Рисунок 1, Рисунок 2, …
    - **Посекционная** нумерация (sectional=True): Рисунок 1.1, Рисунок 1.2, …
      (ГОСТ п. 1.15 — нумерация в пределах раздела)
    """

    def __init__(self, sectional: bool = False):
        self._sectional = sectional
        self._categories: dict[str, int] = defaultdict(lambda: 0)
        self._current_section: int = 0  # номер текущего раздела (Heading level 1)
        self._reference_data: dict[str, str] = dict()  # unique_name -> formatted number

    def _format_number(self, seq: int) -> str:
        """Вернуть отформатированный номер: '3' или '2.3'."""
        if self._sectional and self._current_section > 0:
            return f"{self._current_section}.{seq}"
        return str(seq)

    def process(self, renderables: list[Renderable]):
        for renderable in renderables:
            # Отслеживаем заголовки level 1 для посекционной нумерации
            if isinstance(renderable, Heading) and renderable.level == 1 and renderable.is_numbered:
                self._current_section += 1
                if self._sectional:
                    # Сброс счётчиков категорий при новом разделе
                    self._categories.clear()

            if not isinstance(renderable, RequiresNumbering):
                continue

            requires_numbering = renderable
            self._categories[requires_numbering.numbering_category] += 1
            seq = self._categories[requires_numbering.numbering_category]
            formatted = self._format_number(seq)

            requires_numbering.set_number(formatted)

            if not requires_numbering.numbering_unique_name:
                continue

            if requires_numbering.numbering_unique_name in self._reference_data:
                logging.warning(
                    f"Дублирование названия подписи: {requires_numbering.numbering_unique_name}. "
                    f"Ссылки будут созданы некорректно"
                )
            self._reference_data[requires_numbering.numbering_unique_name] = formatted

        # Вторым проходом разрешаем ссылки
        for paragraph in filter(lambda x: isinstance(x, Paragraph), renderables):
            for reference in paragraph.references:
                if reference.unique_name in self._reference_data:
                    reference.set_number(self._reference_data[reference.unique_name])
                else:
                    logging.warning(f"Неверная ссылка: {reference.unique_name} не существует")
