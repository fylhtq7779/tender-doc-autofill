"""Загрузка и валидация JSON-данных из 3 источников + генерация системных полей.

Классы:
  SystemData   - автогенерируемые поля (дата, номер исходящего)
  DataContext   - контейнер для всех 4 источников данных
  DataLoader    - загрузчик JSON + генератор SystemData
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from src.models import CalcData, CompanyProfile, TenderData
from src.utils import format_date_long

ModelT = TypeVar("ModelT", bound=BaseModel)


class SystemData(BaseModel):
    """Автогенерируемые системные поля (SYSTEM)."""

    current_date: str          # "31.03.2026"
    current_date_long: str     # "«31» марта 2026 года"
    current_year: str          # "2026"
    outgoing_number: str       # "№3103/1"


class DataContext(BaseModel):
    """Контейнер для всех 4 источников данных."""

    profile: CompanyProfile
    tender: TenderData
    calc: CalcData
    system: SystemData


class DataLoader:
    """Загрузчик JSON-данных и генератор системных полей."""

    def __init__(self, data_dir: Path = Path("data")) -> None:
        self._data_dir = data_dir

    def load_all(self) -> DataContext:
        """Загружает все источники и собирает DataContext."""
        profile = self._load_json("company_profile.json", CompanyProfile)
        tender = self._load_json("tender.json", TenderData)
        calc = self._load_json("calc.json", CalcData)
        system = self._generate_system_data()

        return DataContext(
            profile=profile,
            tender=tender,
            calc=calc,
            system=system,
        )

    def _load_json(self, filename: str, model_class: type[ModelT]) -> ModelT:
        """Читает JSON-файл и валидирует через Pydantic-модель.

        Raises:
            FileNotFoundError: если файл не найден (с именем файла в сообщении)
            pydantic.ValidationError: если структура невалидна
        """
        filepath = self._data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Файл данных не найден: {filename} (путь: {filepath})"
            )

        with open(filepath, encoding="utf-8") as f:
            raw = json.load(f)

        return model_class.model_validate(raw)

    def _generate_system_data(self) -> SystemData:
        """Генерирует системные поля на основе текущей даты."""
        now = datetime.now()

        current_date = now.strftime("%d.%m.%Y")
        current_date_long = format_date_long(current_date)
        current_year = now.strftime("%Y")
        # Номер исходящего: №DDMM/1
        outgoing_number = f"№{now.strftime('%d%m')}/1"

        return SystemData(
            current_date=current_date,
            current_date_long=current_date_long,
            current_year=current_year,
            outgoing_number=outgoing_number,
        )
