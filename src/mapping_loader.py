"""Загрузка и парсинг YAML-маппингов документов.

Классы:
  FieldMapping       - описание одного плейсхолдера в документе
  ColumnMapping      - описание одной колонки в табличной строке
  TableRowsMapping   - описание табличных строк (позиции закупки/расчёта)
  DocumentInfo       - метаданные документа (имя, шаблон, выходной файл)
  DocumentMapping    - полный маппинг документа
  MappingLoader      - загрузчик YAML-файлов маппинга
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic-модели маппинга
# ---------------------------------------------------------------------------

class FieldMapping(BaseModel):
    """Описание одного плейсхолдера - поле для подстановки в документе."""

    placeholder: str
    source: str        # PROFILE | TENDER | CALC | SYSTEM
    path: str
    required: bool = False
    transform: str | None = None  # null | date_long | money | money_words


class ColumnMapping(BaseModel):
    """Описание одной колонки в табличной строке."""

    path: str
    source: str | None = None       # переопределение источника для колонки
    items_path: str | None = None   # переопределение items_path для колонки
    transform: str | None = None


class TableRowsMapping(BaseModel):
    """Описание табличных строк - заполнение позиций из массива данных."""

    table_idx: int
    source: str          # CALC или TENDER
    items_path: str      # "items"
    row_start: int       # индекс первой строки данных
    columns: dict[int, ColumnMapping]  # col_idx -> маппинг колонки


class DocumentInfo(BaseModel):
    """Метаданные документа: имя, путь к шаблону, имя выходного файла."""

    name: str
    template: str
    output_name: str


class DocumentMapping(BaseModel):
    """Полный маппинг документа: метаданные + поля + таблицы."""

    document: DocumentInfo
    fields: list[FieldMapping] = []
    table_rows: list[TableRowsMapping] = []


# ---------------------------------------------------------------------------
# Загрузчик маппингов
# ---------------------------------------------------------------------------

class MappingLoader:
    """Загрузчик YAML-файлов маппинга документов."""

    def load(self, path: Path) -> DocumentMapping:
        """Загружает один YAML-маппинг и валидирует через Pydantic.

        Raises:
            FileNotFoundError: если файл не найден
            pydantic.ValidationError: если структура невалидна
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Файл маппинга не найден: {path}"
            )

        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        return DocumentMapping.model_validate(raw)

    def load_all(self, mappings_dir: Path = Path("mappings")) -> list[DocumentMapping]:
        """Загружает все .yaml файлы из директории, отсортированные по имени.

        Returns:
            Список DocumentMapping, отсортированный по имени файла.
        """
        mappings_dir = Path(mappings_dir)
        yaml_files = sorted(mappings_dir.glob("*.yaml"))
        return [self.load(f) for f in yaml_files]
