"""CLI точка входа — команды generate и validate.

Использование:
  python -m src.main generate [--data-dir ...] [--mappings-dir ...] [--output-dir ...]
  python -m src.main validate [--data-dir ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from src.data_loader import DataLoader
from src.generator import DocumentGenerator
from src.utils import format_money


@click.group()
def cli() -> None:
    """Homelio — автозаполнение тендерных DOCX-документов."""


@cli.command()
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(exists=False),
    help="Папка с JSON-данными",
)
@click.option(
    "--mappings-dir",
    default="mappings",
    type=click.Path(exists=False),
    help="Папка с YAML-маппингами",
)
@click.option(
    "--output-dir",
    default="output",
    type=click.Path(exists=False),
    help="Папка для результатов",
)
def generate(data_dir: str, mappings_dir: str, output_dir: str) -> None:
    """Генерация документов по маппингам и данным."""
    try:
        gen = DocumentGenerator(
            data_dir=Path(data_dir),
            mappings_dir=Path(mappings_dir),
            output_dir=Path(output_dir),
        )
        paths = gen.generate_all()
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Сгенерировано {len(paths)} документ(ов):")
    for i, path in enumerate(paths, start=1):
        click.echo(f"  {i}. {path}")


@cli.command()
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(exists=False),
    help="Папка с JSON-данными",
)
def validate(data_dir: str) -> None:
    """Проверка входных JSON-данных."""
    try:
        loader = DataLoader(data_dir=Path(data_dir))
        ctx = loader.load_all()
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    # company_profile.json
    profile = ctx.profile
    click.echo(
        f"company_profile.json: OK "
        f"(ИНН: {profile.company.inn}, БИК: {profile.bank.bik})"
    )

    # tender.json
    tender = ctx.tender
    items_count = len(tender.items)
    click.echo(
        f"tender.json: OK "
        f"({items_count} позиций, заказчик: {tender.customer.short_name})"
    )

    # calc.json
    calc = ctx.calc
    total_str = format_money(calc.total_with_vat)
    vat_str = format_money(calc.vat_amount)
    click.echo(
        f"calc.json: OK "
        f"(итого: {total_str}, НДС: {vat_str})"
    )


if __name__ == "__main__":
    cli()
