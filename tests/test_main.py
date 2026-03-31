"""Тесты для CLI точки входа — команды generate и validate."""

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from docx import Document


# ---------------------------------------------------------------------------
# Фикстуры — создание тестового окружения
# ---------------------------------------------------------------------------

def _create_test_docx(path: Path) -> None:
    """Создаёт минимальный DOCX-шаблон с плейсхолдером."""
    doc = Document()
    doc.add_paragraph("[NAME]")
    doc.save(str(path))


def _create_test_jsons(data_dir: Path) -> None:
    """Создаёт минимальные JSON-файлы для тестов."""
    profile = {
        "company": {
            "full_name": "ООО «Тест»",
            "short_name": "ООО «Тест»",
            "inn": "7705123456",
            "kpp": "770501001",
            "ogrn": "1127746123456",
            "legal_address_full": "Адрес",
            "legal_address_short": "Адрес",
            "postal_address": "Адрес",
            "country": "Россия",
            "city": "Москва",
        },
        "bank": {
            "name": "Банк",
            "account": "40702810900000012345",
            "correspondent_account": "30101810400000000225",
            "bik": "044525225",
        },
        "contact": {
            "responsible_name_full": "Иванов И.И.",
            "responsible_name_short": "Иванов И.И.",
            "phone": "+7 999 000-00-00",
            "email": "test@test.ru",
        },
        "signatory": {
            "position": "Директор",
            "name_short": "Иванов И.И.",
            "name_full": "Иванов Иван Иванович",
            "basis": "Устав",
        },
    }
    tender = {
        "purchase_number": "PUR-001",
        "lot_number": "1",
        "subject": "Поставка кабеля",
        "customer": {
            "full_name": "АО «Заказчик»",
            "short_name": "АО «Заказчик»",
            "legal_address": "Адрес",
            "postal_address": "Адрес",
            "email": "c@c.ru",
            "inn": "5190999900",
            "kpp": "519001001",
            "ogrn": "1145190001234",
            "bank": {
                "name": "Банк",
                "account": "40702810900000012345",
                "correspondent_account": "30101810400000000225",
                "bik": "044525225",
            },
            "signatory": {"position": "Директор", "name": "Иванов И.И."},
        },
        "delivery": {"place": "Москва", "basis": "DAP"},
        "items": [
            {"line_no": 1, "article": "A1", "name": "Кабель", "unit": "м", "qty": 100, "nmc_unit_price": 150.0},
            {"line_no": 2, "article": "A2", "name": "Провод", "unit": "м", "qty": 200, "nmc_unit_price": 250.0},
            {"line_no": 3, "article": "A3", "name": "Муфта", "unit": "шт", "qty": 10, "nmc_unit_price": 500.0},
        ],
    }
    calc = {
        "vat_rate": 0.2,
        "items": [
            {"line_no": 1, "quote_name": "Кабель", "unit_price_wo_vat": 120.0, "line_total_wo_vat": 12000.0},
            {"line_no": 2, "quote_name": "Провод", "unit_price_wo_vat": 200.0, "line_total_wo_vat": 40000.0},
        ],
        "subtotal_wo_vat": 432600.0,
        "vat_amount": 86520.0,
        "total_with_vat": 519120.0,
    }

    for name, data in [
        ("company_profile.json", profile),
        ("tender.json", tender),
        ("calc.json", calc),
    ]:
        (data_dir / name).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )


def _create_test_mapping(
    mappings_dir: Path,
    template_path: str,
    output_name: str,
) -> None:
    """Создаёт минимальный YAML-маппинг."""
    mapping = {
        "document": {
            "name": "Тестовый документ",
            "template": template_path,
            "output_name": output_name,
        },
        "fields": [
            {
                "placeholder": "[NAME]",
                "source": "PROFILE",
                "path": "company.full_name",
            },
        ],
    }
    (mappings_dir / "01_test.yaml").write_text(
        yaml.dump(mapping, allow_unicode=True), encoding="utf-8"
    )


@pytest.fixture()
def cli_env(tmp_path: Path):
    """Подготавливает полное тестовое окружение: данные, шаблон, маппинг."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_test_jsons(data_dir)

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    template_path = templates_dir / "test.docx"
    _create_test_docx(template_path)

    mappings_dir = tmp_path / "mappings"
    mappings_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    _create_test_mapping(mappings_dir, str(template_path), "result.docx")

    return {
        "data_dir": str(data_dir),
        "mappings_dir": str(mappings_dir),
        "output_dir": str(output_dir),
        "output_file": str(output_dir / "result.docx"),
    }


# ---------------------------------------------------------------------------
# Тесты
# ---------------------------------------------------------------------------

class TestGenerate:
    """Тесты для команды generate."""

    def test_generate_creates_files(self, cli_env: dict) -> None:
        """generate создаёт выходные файлы, exit code 0."""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--data-dir", cli_env["data_dir"],
            "--mappings-dir", cli_env["mappings_dir"],
            "--output-dir", cli_env["output_dir"],
        ])

        assert result.exit_code == 0, f"Ошибка: {result.output}"
        assert Path(cli_env["output_file"]).exists()

    def test_generate_output_message(self, cli_env: dict) -> None:
        """generate выводит сообщение с именами сгенерированных файлов."""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--data-dir", cli_env["data_dir"],
            "--mappings-dir", cli_env["mappings_dir"],
            "--output-dir", cli_env["output_dir"],
        ])

        assert result.exit_code == 0
        assert "result.docx" in result.output

    def test_generate_missing_data_dir(self, tmp_path: Path) -> None:
        """generate с несуществующей папкой данных → exit code != 0."""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--data-dir", str(tmp_path / "nonexistent"),
            "--mappings-dir", str(tmp_path / "mappings"),
            "--output-dir", str(tmp_path / "output"),
        ])

        assert result.exit_code != 0


class TestValidate:
    """Тесты для команды validate."""

    def test_validate_success(self, cli_env: dict) -> None:
        """validate с валидными данными → exit code 0."""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "validate",
            "--data-dir", cli_env["data_dir"],
        ])

        assert result.exit_code == 0

    def test_validate_output_contains_info(self, cli_env: dict) -> None:
        """validate выводит ИНН, количество позиций и итого."""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            "validate",
            "--data-dir", cli_env["data_dir"],
        ])

        assert result.exit_code == 0
        # ИНН из company_profile
        assert "7705123456" in result.output
        # БИК из company_profile
        assert "044525225" in result.output
        # Количество позиций tender (3)
        assert "3" in result.output
        # Итого из calc
        assert "519 120,00" in result.output

    def test_validate_missing_file(self, tmp_path: Path) -> None:
        """validate с отсутствующим JSON → exit code != 0."""
        from src.main import cli

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        # Создаём только один файл — остальные отсутствуют
        (data_dir / "company_profile.json").write_text("{}", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "validate",
            "--data-dir", str(data_dir),
        ])

        assert result.exit_code != 0


class TestHelp:
    """Тест для --help."""

    def test_help(self) -> None:
        """--help выводит справку, exit code 0."""
        from src.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "generate" in result.output
        assert "validate" in result.output
