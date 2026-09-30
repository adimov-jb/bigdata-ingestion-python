"""Ingestão de fontes externas para a camada bronze."""

import argparse
import logging
import os
from datetime import UTC, date, datetime, timedelta

from ingestion.catalog import register_local
from ingestion.pipeline import run_source
from ingestion.settings import Settings
from ingestion.source import Source
from ingestion.sources import SOURCES

log = logging.getLogger("ingestion")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingestion", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="Lista as fontes disponíveis")

    run_cmd = commands.add_parser("run", help="Ingere um dia de uma ou mais fontes para a bronze")
    run_cmd.add_argument("sources", nargs="*", metavar="SOURCE", help="Padrão: todas as fontes")
    run_cmd.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date() - timedelta(days=1),
        help="Dia a ingerir, YYYY-MM-DD (padrão: ontem em UTC)",
    )

    register_cmd = commands.add_parser(
        "register-local",
        help="Cria/atualiza as tabelas bronze no Hive Metastore local (equivale ao Glue Crawler)",
    )
    register_cmd.add_argument(
        "sources", nargs="*", metavar="SOURCE", help="Padrão: todas as fontes"
    )
    return parser


def select_sources(names: list[str], parser: argparse.ArgumentParser) -> list[Source]:
    unknown = [name for name in names if name not in SOURCES]
    if unknown:
        parser.error(f"fonte(s) desconhecida(s): {', '.join(unknown)}. Veja `ingestion list`.")
    # Sem nomes: todas. Nomes repetidos rodam uma vez só, na ordem informada.
    return [SOURCES[name] for name in dict.fromkeys(names or SOURCES)]


def run_all(sources: list[Source], day: date, settings: Settings) -> int:
    """Cada fonte roda isolada: a falha de uma não impede as demais."""
    failed = []
    for source in sources:
        try:
            run_source(source, day, settings)
        except Exception:
            log.exception("%s: falhou ao ingerir %s", source.name, day)
            failed.append(source.name)

    if failed:
        log.error("Falharam %d de %d fonte(s): %s", len(failed), len(sources), ", ".join(failed))
        return 1
    log.info("%d fonte(s) ingerida(s) para %s", len(sources), day)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    # Primeira linha do log de toda execução: identifica o código que rodou.
    log.info("bigdata-ingestion commit %s", os.getenv("BIGDATA_VERSION", "dev"))

    if args.command == "list":
        for source in SOURCES.values():
            print(f"{source.name:<20} bronze.{source.table:<35} {source.description}")
        return 0

    sources = select_sources(args.sources, parser)
    settings = Settings.from_env()
    if args.command == "run":
        return run_all(sources, args.date, settings)
    if args.command == "register-local":
        register_local(sources, settings)
    return 0
