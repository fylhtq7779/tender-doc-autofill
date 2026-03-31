"""Тесты для утилит форматирования."""

import pytest

from src.utils import format_date_long, format_money, resolve_dot_path


class TestFormatDateLong:
    """Тесты для format_date_long - преобразование даты в длинный формат."""

    def test_march(self) -> None:
        """Март - родительный падеж."""
        assert format_date_long("31.03.2026") == '«31» марта 2026 года'

    def test_april(self) -> None:
        """Апрель - родительный падеж."""
        assert format_date_long("15.04.2026") == '«15» апреля 2026 года'

    def test_january_leading_zero(self) -> None:
        """Январь с ведущим нулём в дне."""
        assert format_date_long("05.01.2026") == '«05» января 2026 года'

    def test_invalid_date(self) -> None:
        """Невалидная дата - возвращает исходную строку."""
        assert format_date_long("not-a-date") == "not-a-date"


class TestFormatMoney:
    """Тесты для format_money - форматирование денежных сумм."""

    def test_large_amount(self) -> None:
        """Крупная сумма с разделителем тысяч."""
        assert format_money(432600.0) == "432 600,00"

    def test_small_amount(self) -> None:
        """Сумма без тысяч."""
        assert format_money(176.0) == "176,00"

    def test_with_decimal(self) -> None:
        """Сумма с копейками."""
        assert format_money(88.5) == "88,50"

    def test_zero(self) -> None:
        """Ноль."""
        assert format_money(0.0) == "0,00"


class TestResolveDotPath:
    """Тесты для resolve_dot_path - доступ к вложенным данным по точечному пути."""

    def test_nested_key(self) -> None:
        """Вложенный ключ через точку."""
        data = {"company": {"inn": "7712345678"}}
        assert resolve_dot_path(data, "company.inn") == "7712345678"

    def test_array_index(self) -> None:
        """Доступ к элементу массива по индексу."""
        data = {"items": [{"name": "Кабель"}]}
        assert resolve_dot_path(data, "items[0].name") == "Кабель"

    def test_missing_key_returns_none(self) -> None:
        """Отсутствующий ключ - None, без исключений."""
        data = {"company": {"inn": "123"}}
        assert resolve_dot_path(data, "company.kpp") is None

    def test_empty_path_returns_data(self) -> None:
        """Пустой путь - возвращает весь словарь."""
        data = {"a": 1}
        assert resolve_dot_path(data, "") == data
