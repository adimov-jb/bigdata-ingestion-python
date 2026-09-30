"""Registro das tabelas bronze no catálogo local (Hive Metastore via Trino).

Equivale ao Glue Crawler da AWS e só é usado no ambiente local.
"""

import logging
from collections.abc import Sequence

import trino

from ingestion.settings import Settings
from ingestion.source import Source
from ingestion.writer import dataset_path

log = logging.getLogger(__name__)

SCHEMA = "bronze"


def schema_statement(bucket: str) -> str:
    return f"CREATE SCHEMA IF NOT EXISTS hive.{SCHEMA} WITH (location = 's3://{bucket}/')"


def table_statements(source: Source, bucket: str) -> list[str]:
    # IF NOT EXISTS: mudar o schema de uma fonte exige DROP TABLE manual (a tabela é externa,
    # os dados no S3 não são apagados).
    columns = ",\n            ".join(f"{col.name} {col.type}" for col in source.bronze_columns)
    return [
        f"""
        CREATE TABLE IF NOT EXISTS hive.{SCHEMA}.{source.table} (
            {columns}
        )
        WITH (
            format = 'PARQUET',
            external_location = '{dataset_path(bucket, source.dataset)}',
            partitioned_by = ARRAY['dt']
        )
        """,
        # FULL: adiciona partições novas e remove as que sumiram do S3.
        f"CALL hive.system.sync_partition_metadata('{SCHEMA}', '{source.table}', 'FULL')",
    ]


def register_local(sources: Sequence[Source], settings: Settings) -> None:
    conn = trino.dbapi.connect(
        host=settings.trino_host,
        port=settings.trino_port,
        user="ingestion",
        catalog="hive",
    )
    try:
        cursor = conn.cursor()
        statements = [schema_statement(settings.bronze_bucket)]
        for source in sources:
            statements += table_statements(source, settings.bronze_bucket)
        for statement in statements:
            cursor.execute(statement)
            cursor.fetchall()
    finally:
        conn.close()
    for source in sources:
        log.info("Tabela hive.%s.%s registrada e partições sincronizadas", SCHEMA, source.table)
