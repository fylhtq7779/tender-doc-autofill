"""Тесты для DataLoader - загрузка и валидация JSON-данных."""

import json
import re
from pathlib import Path

import pytest

from src.data_loader import DataContext, DataLoader, SystemData


class TestLoadAll:
    """Тесты для DataLoader.load_all - загрузка всех источников."""

    def test_load_all_success(self, tmp_path: Path) -> None:
        """Загрузка 3 JSON + системные данные - все поля доступны."""
        _write_test_jsons(tmp_path)
        loader = DataLoader(data_dir=tmp_path)
        ctx = loader.load_all()

        assert ctx.profile.company.inn == "7705123456"
        assert ctx.tender.purchase_number == "PUR-2026-001"
        assert ctx.calc.vat_rate == 20.0
        assert isinstance(ctx.system, SystemData)

    def test_missing_file(self, tmp_path: Path) -> None:
        """Отсутствующий JSON - FileNotFoundError с именем файла."""
        loader = DataLoader(data_dir=tmp_path)
        with pytest.raises(FileNotFoundError, match="company_profile.json"):
            loader.load_all()

    def test_invalid_json_structure(self, tmp_path: Path) -> None:
        """Невалидная структура JSON - ValidationError."""
        # Пишем JSON без обязательного поля company
        (tmp_path / "company_profile.json").write_text(
            '{"not_company": {}}', encoding="utf-8"
        )
        (tmp_path / "tender.json").write_text(
            '{"purchase_number": "X", "lot_number": "1", "subject": "S", "customer": {"full_name": "C", "short_name": "C", "legal_address": "A", "postal_address": "A", "email": "e@e", "inn": "7705123456", "kpp": "770501001", "ogrn": "1127746123456", "bank": {"name": "B", "account": "40702810900000012345", "correspondent_account": "30101810400000000225", "bik": "044525225"}, "signatory": {"position": "P", "name": "N"}}, "delivery": {"place": "P", "basis": "B"}}',
            encoding="utf-8",
        )
        (tmp_path / "calc.json").write_text(
            '{"vat_rate": 20.0}', encoding="utf-8"
        )
        loader = DataLoader(data_dir=tmp_path)
        with pytest.raises(Exception):
            loader.load_all()


class TestSystemData:
    """Тесты для SystemData - автогенерируемые системные поля."""

    def test_current_date_format(self) -> None:
        """current_date соответствует формату DD.MM.YYYY."""
        loader = DataLoader()
        system = loader._generate_system_data()
        assert re.match(r"\d{2}\.\d{2}\.\d{4}$", system.current_date)

    def test_current_date_long_format(self) -> None:
        """current_date_long содержит кавычки-ёлочки и слово 'года'."""
        loader = DataLoader()
        system = loader._generate_system_data()
        assert "\u00ab" in system.current_date_long
        assert "года" in system.current_date_long

    def test_outgoing_number_format(self) -> None:
        """outgoing_number начинается с '№' и содержит '/'."""
        loader = DataLoader()
        system = loader._generate_system_data()
        assert system.outgoing_number.startswith("№")
        assert "/" in system.outgoing_number


# ---------------------------------------------------------------------------
# Хелперы для создания тестовых JSON-файлов
# ---------------------------------------------------------------------------

def _write_test_jsons(tmp_path: Path) -> None:
    """Создаёт минимальные валидные JSON-файлы для тестов."""
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
            "responsible_name_full": "Петров И.И.",
            "responsible_name_short": "Петров И.И.",
            "phone": "+7 999 000-00-00",
            "email": "test@test.ru",
        },
        "signatory": {
            "position": "Директор",
            "name_short": "Петров И.И.",
            "name_full": "Петров Иван Иванович",
            "basis": "Устав",
        },
    }
    tender = {
        "purchase_number": "PUR-2026-001",
        "lot_number": "1",
        "subject": "Поставка кабеля",
        "customer": {
            "full_name": "АО «Заказчик»",
            "short_name": "АО «Заказчик»",
            "legal_address": "Адрес",
            "postal_address": "Адрес",
            "email": "c@c.ru",
            "inn": "7705123456",
            "kpp": "770501001",
            "ogrn": "1127746123456",
            "bank": {
                "name": "Банк",
                "account": "40702810900000012345",
                "correspondent_account": "30101810400000000225",
                "bik": "044525225",
            },
            "signatory": {"position": "Директор", "name": "Иванов И.И."},
        },
        "delivery": {"place": "Москва", "basis": "DAP"},
    }
    calc = {"vat_rate": 20.0}

    for name, data in [
        ("company_profile.json", profile),
        ("tender.json", tender),
        ("calc.json", calc),
    ]:
        (tmp_path / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
