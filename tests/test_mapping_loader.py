"""Тесты для MappingLoader — загрузка и парсинг YAML-маппингов."""

from pathlib import Path

import pytest
import yaml

from src.mapping_loader import (
    ColumnMapping,
    DocumentInfo,
    DocumentMapping,
    FieldMapping,
    MappingLoader,
    TableRowsMapping,
)


class TestLoadValidMapping:
    """Загрузка корректного YAML-маппинга."""

    def test_load_valid_mapping(self, tmp_path: Path) -> None:
        """Парсинг полного маппинга — все поля, таблицы, документ."""
        mapping_file = tmp_path / "01_anketa.yaml"
        mapping_file.write_text(
            yaml.dump(_full_mapping_data(), allow_unicode=True),
            encoding="utf-8",
        )

        loader = MappingLoader()
        result = loader.load(mapping_file)

        assert isinstance(result, DocumentMapping)
        assert result.document.name == "Анкета участника"
        assert result.document.template == "templates/01_anketa.docx"
        assert result.document.output_name == "01_Анкета_участника.docx"
        assert len(result.fields) == 2
        assert result.fields[0].placeholder == "[Полное наименование]"
        assert result.fields[0].source == "PROFILE"
        assert result.fields[0].path == "company.full_name"
        assert result.fields[0].required is True
        assert result.fields[1].placeholder == "[ИНН]"


class TestLoadAllSorted:
    """Загрузка всех маппингов из директории, отсортированных по имени файла."""

    def test_load_all_sorted(self, tmp_path: Path) -> None:
        """Два YAML-файла — загружаются в алфавитном порядке."""
        # Создаём файлы в обратном порядке
        (tmp_path / "02_zayavka.yaml").write_text(
            yaml.dump(_minimal_mapping_data("Заявка"), allow_unicode=True),
            encoding="utf-8",
        )
        (tmp_path / "01_anketa.yaml").write_text(
            yaml.dump(_minimal_mapping_data("Анкета"), allow_unicode=True),
            encoding="utf-8",
        )

        loader = MappingLoader()
        results = loader.load_all(tmp_path)

        assert len(results) == 2
        assert results[0].document.name == "Анкета"
        assert results[1].document.name == "Заявка"


class TestMissingFile:
    """Обработка отсутствующего файла."""

    def test_missing_file(self) -> None:
        """Несуществующий файл — FileNotFoundError."""
        loader = MappingLoader()
        with pytest.raises(FileNotFoundError):
            loader.load(Path("/nonexistent/mapping.yaml"))


class TestFieldDefaults:
    """Значения по умолчанию для необязательных полей FieldMapping."""

    def test_field_defaults(self, tmp_path: Path) -> None:
        """required=False и transform=None по умолчанию."""
        data = _minimal_mapping_data("Тест")
        data["fields"] = [
            {
                "placeholder": "[Поле]",
                "source": "PROFILE",
                "path": "company.inn",
                # required и transform не указаны
            }
        ]
        mapping_file = tmp_path / "test.yaml"
        mapping_file.write_text(
            yaml.dump(data, allow_unicode=True), encoding="utf-8"
        )

        loader = MappingLoader()
        result = loader.load(mapping_file)

        field = result.fields[0]
        assert field.required is False
        assert field.transform is None


class TestTableRowsParsing:
    """Парсинг секции table_rows с columns."""

    def test_table_rows_parsing(self, tmp_path: Path) -> None:
        """Корректный парсинг table_rows — индексы, columns, override source."""
        data = _full_mapping_data()
        mapping_file = tmp_path / "test.yaml"
        mapping_file.write_text(
            yaml.dump(data, allow_unicode=True), encoding="utf-8"
        )

        loader = MappingLoader()
        result = loader.load(mapping_file)

        assert len(result.table_rows) == 1
        tr = result.table_rows[0]
        assert tr.table_idx == 0
        assert tr.source == "CALC"
        assert tr.items_path == "items"
        assert tr.row_start == 1
        # Проверяем columns
        assert len(tr.columns) == 3
        assert tr.columns[0].path == "line_no"
        assert tr.columns[1].path == "quote_name"
        assert tr.columns[2].path == "unit_price_wo_vat"
        assert tr.columns[2].transform == "money"
        # Проверяем что override source отсутствует у обычных колонок
        assert tr.columns[0].source is None


# ---------------------------------------------------------------------------
# Хелперы для создания тестовых данных маппинга
# ---------------------------------------------------------------------------

def _minimal_mapping_data(name: str = "Тест") -> dict:
    """Минимальный валидный маппинг (без полей и таблиц)."""
    return {
        "document": {
            "name": name,
            "template": "templates/test.docx",
            "output_name": "test.docx",
        },
        "fields": [],
    }


def _full_mapping_data() -> dict:
    """Полный маппинг с полями и table_rows."""
    return {
        "document": {
            "name": "Анкета участника",
            "template": "templates/01_anketa.docx",
            "output_name": "01_Анкета_участника.docx",
        },
        "fields": [
            {
                "placeholder": "[Полное наименование]",
                "source": "PROFILE",
                "path": "company.full_name",
                "required": True,
            },
            {
                "placeholder": "[ИНН]",
                "source": "PROFILE",
                "path": "company.inn",
                "required": True,
            },
        ],
        "table_rows": [
            {
                "table_idx": 0,
                "source": "CALC",
                "items_path": "items",
                "row_start": 1,
                "columns": {
                    0: {"path": "line_no"},
                    1: {"path": "quote_name"},
                    2: {"path": "unit_price_wo_vat", "transform": "money"},
                },
            }
        ],
    }
