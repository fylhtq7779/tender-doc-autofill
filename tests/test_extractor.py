"""Тесты для TenderExtractor - извлечение данных тендера из ТКП DOCX."""

from pathlib import Path

import pytest

from src.extractor import TenderExtractor

# Путь к тестовому документу ТКП (копия в fixtures)
RFQ_PATH = Path("tests/fixtures/rfq_example.docx")


@pytest.fixture()
def rfq_result() -> dict:
    """Извлечённые данные из реального ТКП - кешируем для всех тестов."""
    extractor = TenderExtractor(RFQ_PATH)
    return extractor.extract()


class TestExtractFromRfq:
    """Основные поля тендера из ТКП."""

    def test_extract_main_fields(self, rfq_result: dict) -> None:
        """Номер закупки, лот, предмет извлекаются корректно."""
        assert rfq_result["purchase_number"] == "TEST-2026-001"
        assert rfq_result["lot_number"] == "Лот 1"
        assert rfq_result["lot_code"] == "PE-26-001-L1"
        assert "кабельной продукции" in rfq_result["subject"]
        assert rfq_result["bid_deadline"] == "15.04.2026 18:00 МСК"

    def test_extract_customer(self, rfq_result: dict) -> None:
        """Наименование заказчика из строки 'Заказчик: ...'."""
        customer = rfq_result["customer"]
        assert "Полярная Энергетика" in customer["full_name"]

    def test_extract_delivery_payment_warranty(self, rfq_result: dict) -> None:
        """Условия доставки, оплаты и гарантии."""
        assert "Мурманск" in rfq_result["delivery"]["place"]
        assert "10 календарных дней" in rfq_result["delivery"]["term_text"]
        assert "30 календарных дней" in rfq_result["payment"]["term_text"]
        assert "12 месяцев" in rfq_result["warranty"]["term_text"]


class TestExtractItems:
    """Позиции из таблицы ТКП."""

    def test_items_count(self, rfq_result: dict) -> None:
        """В таблице 3 позиции."""
        assert len(rfq_result["items"]) == 3

    def test_items_first_row(self, rfq_result: dict) -> None:
        """Первая позиция: ВВГнг, цена 185.0."""
        item = rfq_result["items"][0]
        assert "ВВГнг" in item["name"]
        assert item["nmc_unit_price"] == 185.0
        assert item["qty"] == 1200
        assert item["unit"] == "м"
        assert item["article"] == "CAB-001"
        assert item["customer_name_code"] == "0001-PE"

    def test_items_prices(self, rfq_result: dict) -> None:
        """Все цены парсятся корректно (запятая -> точка)."""
        prices = [item["nmc_unit_price"] for item in rfq_result["items"]]
        assert prices == [185.0, 264.0, 92.0]


class TestExtractDefaults:
    """Поля, отсутствующие в ТКП, имеют значения по умолчанию."""

    def test_defaults_for_missing_fields(self, rfq_result: dict) -> None:
        """Поля без источника в ТКП - None или значение по умолчанию."""
        assert rfq_result["currency"] == "RUB"
        assert rfq_result.get("offer_validity_days") is None
        assert rfq_result.get("contract_number") is None
