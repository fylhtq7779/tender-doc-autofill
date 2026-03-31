"""Тесты для Pydantic-моделей данных."""

import json
import logging
from pathlib import Path

import pytest

from src.models import CalcData, CompanyProfile, TenderData

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestCompanyProfile:
    """Тесты для модели CompanyProfile."""

    def test_company_profile_valid(self) -> None:
        """Загрузка company_profile.json - все поля на месте."""
        raw = json.loads((DATA_DIR / "company_profile.json").read_text(encoding="utf-8"))
        profile = CompanyProfile.model_validate(raw)

        assert profile.company.full_name == "Общество с ограниченной ответственностью «НордТехРесурс»"
        assert profile.company.inn == "7705123456"
        assert profile.company.kpp == "770501001"
        assert profile.company.ogrn == "1127746123456"
        assert profile.bank.bik == "044525225"
        assert profile.bank.account == "40702810900000012345"
        assert profile.contact.email == "tender@test-supplier.example"
        assert profile.signatory.name_full == "Соколов Иван Андреевич"
        assert profile.compliance.similar_supply_experience_years == 7
        assert len(profile.references) == 3
        assert profile.references[0].customer == "АО «Северный монтаж»"

    def test_optional_field_missing(self) -> None:
        """Отсутствие необязательного поля references - модель загружается."""
        raw = json.loads((DATA_DIR / "company_profile.json").read_text(encoding="utf-8"))
        del raw["references"]
        profile = CompanyProfile.model_validate(raw)

        assert profile.references == []

    def test_meta_field_ignored(self) -> None:
        """Поле _meta из JSON игнорируется без ошибки."""
        raw = json.loads((DATA_DIR / "company_profile.json").read_text(encoding="utf-8"))
        assert "_meta" in raw
        profile = CompanyProfile.model_validate(raw)
        assert not hasattr(profile, "_meta")


class TestTenderData:
    """Тесты для модели TenderData."""

    def test_tender_data_valid(self) -> None:
        """Загрузка tender.json - вложенный customer + 3 позиции."""
        raw = json.loads((DATA_DIR / "tender.json").read_text(encoding="utf-8"))
        tender = TenderData.model_validate(raw)

        assert tender.purchase_number == "TEST-2026-001"
        assert tender.lot_number == "Лот 1"
        assert tender.customer.full_name == "Акционерное общество «Полярная Энергетика»"
        assert tender.customer.inn == "5190999900"
        assert tender.customer.bank.bik == "044705607"
        assert tender.customer.signatory.name == "Орлов Дмитрий Анатольевич"
        assert tender.delivery.basis == "DDP склад заказчика"
        assert len(tender.items) == 3
        assert tender.items[0].name == "Кабель силовой ВВГнг(А)-LS 3х2,5"
        assert tender.items[1].qty == 600

    def test_optional_warranty_missing(self) -> None:
        """Отсутствие warranty - модель загружается."""
        raw = json.loads((DATA_DIR / "tender.json").read_text(encoding="utf-8"))
        del raw["warranty"]
        tender = TenderData.model_validate(raw)
        assert tender.warranty is None


class TestCalcData:
    """Тесты для модели CalcData."""

    def test_calc_data_valid(self) -> None:
        """Загрузка calc.json - итоги совпадают."""
        raw = json.loads((DATA_DIR / "calc.json").read_text(encoding="utf-8"))
        calc = CalcData.model_validate(raw)

        assert calc.vat_rate == 0.2
        assert calc.subtotal_wo_vat == 432600.0
        assert calc.vat_amount == 86520.0
        assert calc.total_with_vat == 519120.0
        assert len(calc.items) == 3
        assert calc.items[0].offer_name == "Кабель силовой ВВГнг(А)-LS 3х2,5"
        assert calc.items[2].manufacturer == "ООО «ПроводТест»"


class TestRequisiteValidation:
    """Тесты валидации реквизитов (ИНН, БИК и т.д.)."""

    def test_inn_valid_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Валидный ИНН (10 цифр) - без предупреждений."""
        raw = json.loads((DATA_DIR / "company_profile.json").read_text(encoding="utf-8"))
        with caplog.at_level(logging.WARNING):
            profile = CompanyProfile.model_validate(raw)
        # Нет предупреждений об ИНН
        assert not any("ИНН" in msg for msg in caplog.messages)
        assert profile.company.inn == "7705123456"

    def test_inn_invalid_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Невалидный ИНН (3 цифры) - warning в лог, но модель создаётся."""
        raw = json.loads((DATA_DIR / "company_profile.json").read_text(encoding="utf-8"))
        raw["company"]["inn"] = "123"
        with caplog.at_level(logging.WARNING):
            profile = CompanyProfile.model_validate(raw)
        assert profile.company.inn == "123"
        assert any("ИНН" in msg for msg in caplog.messages)
