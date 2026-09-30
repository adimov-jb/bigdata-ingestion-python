"""Registro da tabela bronze no catálogo local (Hive Metastore via Trino).

Equivale ao Glue Crawler da AWS e só é usado no ambiente local.
"""

import logging

import trino

from ingestion.config import Settings
from ingestion.writer import dataset_path

log = logging.getLogger(__name__)

SCHEMA = "bronze"
TABLE = "open_meteo_weather_hourly"


def bronze_statements(bucket: str) -> list[str]:
    return [
        f"CREATE SCHEMA IF NOT EXISTS hive.{SCHEMA} WITH (location = 's3://{bucket}/')",
        f"""
        CREATE TABLE IF NOT EXISTS hive.{SCHEMA}.{TABLE} (
            city varchar,
            latitude double,
            longitude double,
            observed_at timestamp(3),
            temperature_2m double,
            relative_humidity_2m double,
            precipitation double,
            wind_speed_10m double,
            weather_code bigint,
            ingested_at timestamp(3),
            dt varchar
        )
        WITH (
            format = 'PARQUET',
            external_location = '{dataset_path(bucket)}',
            partitioned_by = ARRAY['dt']
        )
        """,
        # FULL: adiciona partições novas e remove as que sumiram do S3.
        f"CALL hive.system.sync_partition_metadata('{SCHEMA}', '{TABLE}', 'FULL')",
    ]


def register_bronze_local(settings: Settings) -> None:
    conn = trino.dbapi.connect(
        host=settings.trino_host,
        port=settings.trino_port,
        user="ingestion",
        catalog="hive",
    )
    try:
        cursor = conn.cursor()
        for statement in bronze_statements(settings.bronze_bucket):
            cursor.execute(statement)
            cursor.fetchall()
    finally:
        conn.close()
    log.info("Tabela hive.%s.%s registrada e partições sincronizadas", SCHEMA, TABLE)
