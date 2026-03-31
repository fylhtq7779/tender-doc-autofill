[![CI](https://github.com/fylhtq7779/tender-doc-autofill/actions/workflows/ci.yml/badge.svg)](https://github.com/fylhtq7779/tender-doc-autofill/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Homelio Test — Автозаполнение тендерных документов

Система автоматической генерации тендерных DOCX-документов из структурированных JSON-данных.
Каждое поле в шаблоне заполняется детерминированно по YAML-маппингу — без LLM и без выдумывания значений.

## Быстрый старт

### Требования

- Python 3.11+

### Установка

```bash
git clone https://github.com/fylhtq7779/tender-doc-autofill.git
cd tender-doc-autofill
pip install -e .
```

### Запуск генерации

```bash
python -m src generate
```

### Пример вывода

```
Сгенерировано 4 документ(ов):
  1. output/01_Анкета_участника.docx
  2. output/02_Заявка_на_участие_в_закупке.docx
  3. output/03_Предложение_о_цене_договора.docx
  4. output/04_Гарантийное_письмо.docx
```

### Проверка результата

```bash
# Убедиться что файлы созданы
ls output/

# Визуально сравнить с эталонами
# Эталоны: Материалы/03. Заполненные примеры/
```

## Структура проекта

```
Homelio_test/
├── src/
│   ├── main.py              — CLI (команды generate, validate, extract-tender)
│   ├── generator.py         — координатор генерации документов
│   ├── template_engine.py   — замена плейсхолдеров в DOCX, заполнение таблиц
│   ├── data_loader.py       — загрузка JSON + генерация системных полей
│   ├── mapping_loader.py    — парсинг YAML-маппингов
│   ├── models.py            — Pydantic-модели (CompanyProfile, TenderData, CalcData)
│   ├── utils.py             — форматирование дат, сумм, dot-path резолвер
│   └── extractor.py         — (бонус) извлечение tender.json из DOCX ТКП
├── mappings/
│   ├── 01_anketa.yaml       — маппинг анкеты участника
│   ├── 02_zayavka.yaml      — маппинг заявки на участие
│   ├── 03_predlozhenie.yaml — маппинг предложения о цене
│   └── 04_garantiya.yaml    — маппинг гарантийного письма
├── data/
│   ├── company_profile.json — реквизиты компании-участника
│   ├── tender.json          — данные закупки (номер, заказчик, позиции)
│   └── calc.json            — расчёт цены (позиции, НДС, итоги)
├── templates/               — DOCX-шаблоны с плейсхолдерами
├── output/                  — сгенерированные документы
├── tests/                   — unit и integration тесты (58 тестов)
└── docs/
    └── architecture.md      — записка по архитектуре
```

## Маппинг-конфиги

Каждый документ описывается YAML-файлом в `mappings/`. Формат:

```yaml
document:
  name: "Анкета участника"
  template: "templates/01_anketa.docx"
  output_name: "01_Анкета_участника.docx"

fields:
  - placeholder: "[ИНН]"
    source: PROFILE          # PROFILE | TENDER | CALC | SYSTEM
    path: "company.inn"      # dot-path к полю в JSON
    required: true           # если не найдено → [НЕ УКАЗАНО]

  - placeholder: "[Дата]"
    source: SYSTEM
    path: "current_date_long"
    transform: "date_long"   # null | date_long | money

table_rows:
  - table_idx: 1             # индекс таблицы в документе
    source: CALC
    items_path: "items"
    row_start: 1             # индекс первой строки данных
    columns:
      0: { path: "line_no" }
      1: { path: "offer_name" }
      4: { path: "unit_price_with_delivery_w_vat", transform: "money" }
```

**Источники данных:**

| Источник | Файл | Содержание |
|----------|------|------------|
| `PROFILE` | `data/company_profile.json` | Реквизиты компании, банк, контакт, подписант |
| `TENDER` | `data/tender.json` | Номер закупки, заказчик, позиции, условия |
| `CALC` | `data/calc.json` | Расчёт цены, НДС, итоги по позициям |
| `SYSTEM` | автогенерация | Текущая дата, номер исходящего |

## Доступные команды

```bash
# Генерация всех документов
python -m src generate

# Генерация с переопределением директорий
python -m src generate --data-dir my_data --output-dir my_output

# Проверка и валидация входных JSON
python -m src validate

# (бонус) Извлечение tender.json из DOCX-документа ТКП
python -m src extract-tender "Материалы/01. Входящий документ от заказчика/ТКП.docx"

# Справка по любой команде
python -m src generate --help
```

## Как добавить новый документ

Добавление нового документа не требует изменений в коде:

1. Поместить DOCX-шаблон в `templates/05_novyi.docx`
2. Создать `mappings/05_novyi.yaml` по аналогии с существующими маппингами
3. Запустить `python -m src generate`

Новый файл автоматически появится в `output/`.

## Тесты

```bash
# Все тесты
pytest tests/ -q

# Конкретный модуль
pytest tests/test_template_engine.py --tb=short

# С покрытием
pytest tests/ --cov=src --cov-report=term-missing
```

Текущий результат: **58 тестов, 100% прохождение**.

## Архитектура (кратко)

```
data/*.json     ──►  DataLoader     ──►  DataContext
mappings/*.yaml ──►  MappingLoader  ──►  DocumentMapping
                                                │
                                           Generator
                                                │
                               ┌────────────────┴──────────────────┐
                          resolve_field                  fill_table_rows
                               │                                │
                          TemplateEngine  ◄────────────────────────
                               │
                          output/*.docx
```

Подробнее: [`docs/architecture.md`](docs/architecture.md)
