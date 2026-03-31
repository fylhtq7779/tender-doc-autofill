"""Pydantic-модели для 3 источников данных: CompanyProfile, TenderData, CalcData.

Все поля соответствуют структуре JSON-файлов из data/.
Необязательные поля имеют значения по умолчанию.
Валидация реквизитов (ИНН, КПП, ОГРН, БИК, р/с) - через warning в лог.
"""

import logging
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Утилиты валидации реквизитов
# ---------------------------------------------------------------------------

def _warn_if_not_digits(value: str | None, field_name: str, expected_len: int | tuple[int, ...]) -> str:
    """Проверяет что строка состоит из цифр заданной длины. Логирует warning при несоответствии."""
    if value is None:
        return ""
    if not value:
        return value
    lengths = (expected_len,) if isinstance(expected_len, int) else expected_len
    if not value.isdigit() or len(value) not in lengths:
        expected = " или ".join(str(ln) for ln in lengths)
        logger.warning(
            "%s '%s' невалиден: ожидается %s цифр, получено %d символов",
            field_name, value, expected, len(value),
        )
    return value


# ---------------------------------------------------------------------------
# CompanyProfile (PROFILE)
# ---------------------------------------------------------------------------

class Company(BaseModel):
    """Реквизиты компании-участника."""

    model_config = ConfigDict(extra="ignore")

    full_name: str = ""
    short_name: str = ""
    inn: Optional[str] = ""
    kpp: Optional[str] = ""
    ogrn: Optional[str] = ""
    legal_address_full: Optional[str] = ""
    legal_address_short: Optional[str] = ""
    postal_address: Optional[str] = ""
    country: Optional[str] = ""
    city: Optional[str] = ""

    @field_validator("inn", mode="before")
    @classmethod
    def validate_inn(cls, v: str | None) -> str:
        """ИНН: 10 (юрлицо) или 12 (физлицо) цифр."""
        return _warn_if_not_digits(v, "ИНН", (10, 12))

    @field_validator("kpp", mode="before")
    @classmethod
    def validate_kpp(cls, v: str | None) -> str:
        """КПП: 9 символов."""
        return _warn_if_not_digits(v, "КПП", 9)

    @field_validator("ogrn", mode="before")
    @classmethod
    def validate_ogrn(cls, v: str | None) -> str:
        """ОГРН: 13 цифр."""
        return _warn_if_not_digits(v, "ОГРН", 13)


class Bank(BaseModel):
    """Банковские реквизиты."""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = ""
    account: Optional[str] = ""
    correspondent_account: Optional[str] = ""
    bik: Optional[str] = ""

    @field_validator("bik", mode="before")
    @classmethod
    def validate_bik(cls, v: str | None) -> str:
        """БИК: 9 цифр."""
        return _warn_if_not_digits(v, "БИК", 9)

    @field_validator("account", "correspondent_account", mode="before")
    @classmethod
    def validate_account(cls, v: str | None) -> str:
        """Расчётный/корреспондентский счёт: 20 цифр."""
        return _warn_if_not_digits(v, "Счёт", 20)


class Contact(BaseModel):
    """Контактное лицо."""

    model_config = ConfigDict(extra="ignore")

    responsible_name_full: str = ""
    responsible_name_short: str = ""
    phone: str = ""
    email: str = ""


class Signatory(BaseModel):
    """Подписант компании-участника."""

    model_config = ConfigDict(extra="ignore")

    position: str = ""
    name_short: str = ""
    name_full: str = ""
    basis: str = ""


class Compliance(BaseModel):
    """Комплаенс-информация."""

    model_config = ConfigDict(extra="ignore")

    manufacturer_or_authorized_rep: str = ""
    similar_supply_experience_years: int = 0
    unresolved_claims_absence_confirmed: str = ""
    technical_audit_consent: str = ""
    bankruptcy_absence_confirmed: str = ""
    tax_debt_absence_confirmed: str = ""


class Reference(BaseModel):
    """Референс (запись об опыте поставок)."""

    model_config = ConfigDict(extra="ignore")

    subject: str
    customer: str
    amount_rub: str
    date_range: str
    role_and_scope: str
    claims_info: str = ""
    feedback_attached: str = ""


class CompanyProfile(BaseModel):
    """Корневая модель - профиль компании (PROFILE)."""

    model_config = ConfigDict(extra="ignore")

    company: Company
    bank: Bank
    contact: Contact
    signatory: Signatory
    compliance: Optional[Compliance] = None
    references: list[Reference] = []


# ---------------------------------------------------------------------------
# TenderData (TENDER)
# ---------------------------------------------------------------------------

class CustomerBank(BaseModel):
    """Банковские реквизиты заказчика."""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = ""
    account: Optional[str] = ""
    correspondent_account: Optional[str] = ""
    bik: Optional[str] = ""

    @field_validator("bik", mode="before")
    @classmethod
    def validate_bik(cls, v: str | None) -> str:
        return _warn_if_not_digits(v, "БИК", 9)

    @field_validator("account", "correspondent_account", mode="before")
    @classmethod
    def validate_account(cls, v: str | None) -> str:
        return _warn_if_not_digits(v, "Счёт", 20)


class CustomerSignatory(BaseModel):
    """Подписант заказчика."""

    model_config = ConfigDict(extra="ignore")

    position: str = ""
    name: str = ""


class Customer(BaseModel):
    """Данные заказчика."""

    model_config = ConfigDict(extra="ignore")

    full_name: Optional[str] = ""
    short_name: Optional[str] = ""
    legal_address: Optional[str] = ""
    postal_address: Optional[str] = ""
    email: Optional[str] = ""
    inn: Optional[str] = ""
    kpp: Optional[str] = ""
    ogrn: Optional[str] = ""
    bank: Optional[CustomerBank] = None
    signatory: Optional[CustomerSignatory] = None

    @field_validator("inn", mode="before")
    @classmethod
    def validate_inn(cls, v: str | None) -> str:
        return _warn_if_not_digits(v, "ИНН", (10, 12))

    @field_validator("kpp", mode="before")
    @classmethod
    def validate_kpp(cls, v: str | None) -> str:
        return _warn_if_not_digits(v, "КПП", 9)

    @field_validator("ogrn", mode="before")
    @classmethod
    def validate_ogrn(cls, v: str | None) -> str:
        return _warn_if_not_digits(v, "ОГРН", 13)


class Delivery(BaseModel):
    """Условия доставки."""

    model_config = ConfigDict(extra="ignore")

    place: Optional[str] = ""
    basis: Optional[str] = ""
    start_text: Optional[str] = ""
    end_text: Optional[str] = ""
    term_text: Optional[str] = ""


class Payment(BaseModel):
    """Условия оплаты."""

    model_config = ConfigDict(extra="ignore")

    term_text: Optional[str] = ""


class Warranty(BaseModel):
    """Гарантийные условия."""

    model_config = ConfigDict(extra="ignore")

    term_text: Optional[str] = ""


class TenderItem(BaseModel):
    """Позиция закупки."""

    model_config = ConfigDict(extra="ignore")

    line_no: int = 0
    article: Optional[str] = ""
    name: Optional[str] = ""
    unit: Optional[str] = ""
    qty: int | float = 0
    nmc_unit_price: float = 0.0
    required_delivery_date: Optional[str] = ""
    customer_name_code: Optional[str] = ""
    customer_org: Optional[str] = ""
    basis: Optional[str] = ""


class TenderData(BaseModel):
    """Корневая модель - данные тендера (TENDER)."""

    model_config = ConfigDict(extra="ignore")

    purchase_number: Optional[str] = ""
    lot_number: Optional[str] = ""
    lot_code: Optional[str] = ""
    subject: Optional[str] = ""
    bid_deadline: Optional[str] = ""
    offer_validity_days: Optional[int] = 0
    contract_number: Optional[str] = ""
    currency: Optional[str] = "RUB"
    customer: Optional[Customer] = None
    delivery: Optional[Delivery] = None
    payment: Optional[Payment] = None
    warranty: Optional[Warranty] = None
    items: list[TenderItem] = []


# ---------------------------------------------------------------------------
# CalcData (CALC)
# ---------------------------------------------------------------------------

class CalcItem(BaseModel):
    """Позиция расчёта цены."""

    model_config = ConfigDict(extra="ignore")

    line_no: int
    quote_name: str = ""
    unit_price_wo_vat: float = 0.0
    line_total_wo_vat: float = 0.0
    offer_article: str = ""
    note: str = ""
    offer_spec: str = ""
    country_of_origin: str = ""
    manufacturer: str = ""
    offer_name: str = ""
    offer_unit: str = ""
    offer_qty: int | float = 0
    offer_delivery_date: str = ""
    delivery_price_wo_vat: float = 0.0
    unit_price_with_delivery_wo_vat: float = 0.0
    line_total_w_vat: float = 0.0
    unit_price_with_delivery_w_vat: float = 0.0
    note_kp: str = ""


class CalcData(BaseModel):
    """Корневая модель - расчёт цены (CALC)."""

    model_config = ConfigDict(extra="ignore")

    vat_rate: float
    items: list[CalcItem] = []
    subtotal_wo_vat: float = 0.0
    vat_amount: float = 0.0
    total_with_vat: float = 0.0
