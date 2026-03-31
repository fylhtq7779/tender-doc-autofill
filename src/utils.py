"""Утилиты форматирования: даты, суммы, доступ по dot-path."""

from __future__ import annotations

import re
from typing import Any


# Названия месяцев в родительном падеже (индекс = номер месяца)
_MONTHS_GENITIVE: list[str] = [
    "",  # 0 - не используется
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

# Регулярка для разбора элемента пути с индексом массива: "items[0]"
_ARRAY_INDEX_RE = re.compile(r"^([a-zA-Z_]\w*)\[(\d+)\]$")


def format_date_long(date_str: str) -> str:
    """Преобразует дату из формата DD.MM.YYYY в длинный формат.

    Пример: "31.03.2026" -> '«31» марта 2026 года'
    При невалидном формате возвращает исходную строку.
    """
    parts = date_str.split(".")
    if len(parts) != 3:
        return date_str

    try:
        day, month_num, year = parts[0], int(parts[1]), parts[2]
    except ValueError:
        return date_str

    if not (1 <= month_num <= 12):
        return date_str

    month_name = _MONTHS_GENITIVE[month_num]
    return f"\u00ab{day}\u00bb {month_name} {year} года"


def format_money(amount: float) -> str:
    """Форматирует денежную сумму: разделитель тысяч - пробел, дробная часть - запятая.

    Пример: 432600.0 -> "432 600,00"
    Всегда 2 знака после запятой.
    """
    # Разделяем целую и дробную части
    integer_part = int(amount)
    # Округляем копейки до 2 знаков
    fractional = round(amount - integer_part, 2)
    cents = round(fractional * 100)

    # Форматируем целую часть с пробелами-разделителями тысяч
    int_str = f"{integer_part:,}".replace(",", " ")

    return f"{int_str},{cents:02d}"


def resolve_dot_path(data: dict[str, Any], path: str) -> Any:
    """Извлекает значение из вложенного словаря по точечному пути.

    Поддерживает:
      - вложенные ключи: "company.inn"
      - индексы массивов: "items[0].name"
      - пустой путь: возвращает весь словарь

    При отсутствии ключа возвращает None (без исключений).
    """
    if not path:
        return data

    current: Any = data

    for segment in path.split("."):
        if current is None:
            return None

        # Проверяем наличие индекса массива в сегменте
        match = _ARRAY_INDEX_RE.match(segment)
        if match:
            key, index = match.group(1), int(match.group(2))
            # Доступ к ключу словаря
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            # Доступ по индексу массива
            if isinstance(current, list) and 0 <= index < len(current):
                current = current[index]
            else:
                return None
        else:
            # Простой ключ словаря
            if isinstance(current, dict):
                current = current.get(segment)
            else:
                return None

    return current
