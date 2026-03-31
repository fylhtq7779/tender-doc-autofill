"""Генератор документов: загрузка данных и маппингов, подстановка в DOCX.

Класс DocumentGenerator координирует процесс:
  1. Загрузка данных (DataLoader) и маппингов (MappingLoader)
  2. Для каждого маппинга: подстановка полей и заполнение таблиц
  3. Сохранение результата в output-директорию
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.data_loader import DataContext, DataLoader
from src.mapping_loader import (
    DocumentMapping,
    FieldMapping,
    MappingLoader,
    TableRowsMapping,
)
from src.template_engine import TemplateEngine
from src.utils import format_date_long, format_money, resolve_dot_path

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Генератор документов по маппингу из YAML-конфигов."""

    def __init__(
        self,
        data_dir: Path = Path("data"),
        mappings_dir: Path = Path("mappings"),
        output_dir: Path = Path("output"),
    ) -> None:
        self._data_dir = Path(data_dir)
        self._mappings_dir = Path(mappings_dir)
        self._output_dir = Path(output_dir)

    def generate_all(self) -> list[Path]:
        """Генерирует все документы из всех маппингов.

        Returns:
            Список путей к сгенерированным файлам
        """
        context = self._load_data()
        mappings = self._load_mappings()

        results: list[Path] = []
        for mapping in mappings:
            path = self.generate_document(mapping, context)
            results.append(path)
            logger.info("Сгенерирован: %s", path)

        return results

    def generate_document(
        self, mapping: DocumentMapping, context: DataContext
    ) -> Path:
        """Генерирует один документ по маппингу.

        Args:
            mapping: конфигурация документа (поля, таблицы, метаданные)
            context: контейнер всех источников данных

        Returns:
            Путь к сгенерированному файлу
        """
        # 1. Загружаем шаблон
        template_path = Path(mapping.document.template)
        engine = TemplateEngine(template_path)

        # 2. Обрабатываем поля (плейсхолдеры)
        for field in mapping.fields:
            str_value = self._resolve_field(field, context)
            engine.replace_placeholder(field.placeholder, str_value)

        # 3. Обрабатываем табличные строки
        for table_row in mapping.table_rows:
            self._fill_table_rows(engine, table_row, context)

        # 4. Сохраняем результат
        output_path = self._output_dir / mapping.document.output_name
        engine.save(output_path)

        return output_path

    # ------------------------------------------------------------------
    # Загрузка данных и маппингов
    # ------------------------------------------------------------------

    def _load_data(self) -> DataContext:
        """Загружает все JSON-источники и системные данные."""
        loader = DataLoader(data_dir=self._data_dir)
        return loader.load_all()

    def _load_mappings(self) -> list[DocumentMapping]:
        """Загружает все YAML-маппинги из директории."""
        loader = MappingLoader()
        return loader.load_all(self._mappings_dir)

    # ------------------------------------------------------------------
    # Обработка полей
    # ------------------------------------------------------------------

    def _resolve_field(self, field: FieldMapping, context: DataContext) -> str:
        """Извлекает значение поля из источника и применяет трансформацию.

        Если значение не найдено:
          - required=True → "[НЕ УКАЗАНО]" + warning в лог
          - required=False → пустая строка
        """
        source_data = self._get_source_data(field.source, context)
        value = resolve_dot_path(source_data, field.path)

        if value is None:
            if field.required:
                logger.warning(
                    "Обязательное поле '%s' (путь: %s.%s) не найдено — подставлен маркер",
                    field.placeholder,
                    field.source,
                    field.path,
                )
                return "[НЕ УКАЗАНО]"
            return ""

        return self._apply_transform(value, field.transform)

    def _get_source_data(self, source: str, context: DataContext) -> dict[str, Any]:
        """Возвращает словарь данных по имени источника."""
        source_map = {
            "PROFILE": context.profile,
            "TENDER": context.tender,
            "CALC": context.calc,
            "SYSTEM": context.system,
        }
        model = source_map.get(source)
        if model is None:
            logger.warning("Неизвестный источник данных: %s", source)
            return {}
        return model.model_dump()

    def _apply_transform(self, value: Any, transform: str | None) -> str:
        """Применяет трансформацию к значению.

        Поддерживаемые трансформации:
          - None → str(value)
          - "date_long" → format_date_long(str(value))
          - "money" → format_money(float(value))
        """
        if transform is None:
            return str(value)

        if transform == "date_long":
            return format_date_long(str(value))

        if transform == "money":
            try:
                return format_money(float(value))
            except (ValueError, TypeError):
                logger.warning(
                    "Не удалось применить трансформацию 'money' к значению: %s",
                    value,
                )
                return str(value)

        logger.warning("Неизвестная трансформация: %s", transform)
        return str(value)

    # ------------------------------------------------------------------
    # Обработка таблиц
    # ------------------------------------------------------------------

    def _fill_table_rows(
        self,
        engine: TemplateEngine,
        table_row: TableRowsMapping,
        context: DataContext,
    ) -> None:
        """Заполняет табличные строки данными из массива items."""
        # Получаем основной массив items
        source_data = self._get_source_data(table_row.source, context)
        items = resolve_dot_path(source_data, table_row.items_path)

        if not isinstance(items, list):
            logger.warning(
                "items_path '%s.%s' не является массивом",
                table_row.source,
                table_row.items_path,
            )
            return

        for i, item in enumerate(items):
            row_idx = table_row.row_start + i
            col_values: dict[int, str] = {}

            for col_idx, col_mapping in table_row.columns.items():
                # Определяем источник данных для колонки
                if col_mapping.source and col_mapping.items_path:
                    # Переопределённый источник и items_path для колонки
                    col_source_data = self._get_source_data(
                        col_mapping.source, context
                    )
                    col_items = resolve_dot_path(
                        col_source_data, col_mapping.items_path
                    )
                    if isinstance(col_items, list) and i < len(col_items):
                        cell_value = resolve_dot_path(
                            col_items[i] if isinstance(col_items[i], dict) else {},
                            col_mapping.path,
                        )
                    else:
                        cell_value = None
                else:
                    # Стандартный путь: из текущего item
                    cell_value = resolve_dot_path(
                        item if isinstance(item, dict) else {},
                        col_mapping.path,
                    )

                # Применяем трансформацию
                if cell_value is None:
                    col_values[col_idx] = ""
                else:
                    col_values[col_idx] = self._apply_transform(
                        cell_value, col_mapping.transform
                    )

            try:
                engine.fill_table_row(table_row.table_idx, row_idx, col_values)
            except IndexError:
                logger.warning(
                    "Строка %d выходит за пределы таблицы %d — пропускаем",
                    row_idx,
                    table_row.table_idx,
                )
                break
