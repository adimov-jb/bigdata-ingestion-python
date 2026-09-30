"""Execução de uma fonte: extract → metadados e validação de schema → bronze."""

import logging
from datetime import UTC, date, datetime

import pandas as pd

from ingestion.settings import Settings
from ingestion.source import Source
from ingestion.writer import write_bronze

log = logging.getLogger(__name__)


def with_metadata(
    df: pd.DataFrame, source: Source, day: date, ingested_at: datetime
) -> pd.DataFrame:
    """Confere o schema devolvido pela fonte e adiciona ingested_at e dt."""
    expected = [column.name for column in source.columns]
    missing = [name for name in expected if name not in df.columns]
    extra = [name for name in df.columns if name not in expected]
    if missing or extra:
        raise ValueError(f"{source.name}: schema inválido (faltando={missing}, sobrando={extra})")
    if df.empty:
        raise ValueError(f"{source.name}: nenhuma linha para {day}")

    # Bronze guarda timestamps em UTC, sem timezone.
    ingested = pd.Timestamp(ingested_at)
    if ingested.tzinfo is not None:
        ingested = ingested.tz_convert(None)

    df = df[expected].copy()
    df["ingested_at"] = ingested
    df["dt"] = day.isoformat()
    return df


def run_source(
    source: Source,
    day: date,
    settings: Settings,
    ingested_at: datetime | None = None,
) -> list[str]:
    log.info("%s: ingerindo %s", source.name, day)
    df = source.extract(day)
    df = with_metadata(df, source, day, ingested_at or datetime.now(UTC))
    return write_bronze(df, settings.bronze_bucket, source.dataset, settings.aws_endpoint_url)
