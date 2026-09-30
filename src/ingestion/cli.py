"""Ingestão da API Open-Meteo para a camada bronze."""

import argparse
import logging
from datetime import UTC, date, datetime, timedelta

from ingestion.catalog import register_bronze_local
from ingestion.client import fetch_hourly
from ingestion.config import LOCATIONS, Settings
from ingestion.transform import to_dataframe
from ingestion.writer import write_bronze

log = logging.getLogger("ingestion")


def run(day: date, settings: Settings) -> None:
    payload = fetch_hourly(day, LOCATIONS)
    df = to_dataframe(payload, LOCATIONS, day, ingested_at=datetime.now(UTC))
    write_bronze(df, settings.bronze_bucket, settings.aws_endpoint_url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingestion", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    run_cmd = commands.add_parser("run", help="Ingere um dia da API para a bronze")
    run_cmd.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date() - timedelta(days=1),
        help="Dia a ingerir, YYYY-MM-DD (padrão: ontem em UTC)",
    )

    commands.add_parser(
        "register-local",
        help="Cria/atualiza a tabela bronze no Hive Metastore local (equivalente ao Glue Crawler)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()

    if args.command == "run":
        run(args.date, settings)
    elif args.command == "register-local":
        register_bronze_local(settings)
    return 0
