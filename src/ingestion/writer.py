"""Gravação na camada bronze: Parquet particionado por dt."""

import logging

import awswrangler as wr
import pandas as pd

from ingestion.config import DATASET_PREFIX

log = logging.getLogger(__name__)


def dataset_path(bucket: str) -> str:
    return f"s3://{bucket}/{DATASET_PREFIX}/"


def write_bronze(df: pd.DataFrame, bucket: str, endpoint_url: str | None = None) -> list[str]:
    """Substitui só as partições presentes no DataFrame: reexecutar um dia é idempotente."""
    if endpoint_url:
        wr.config.s3_endpoint_url = endpoint_url

    result = wr.s3.to_parquet(
        df=df,
        path=dataset_path(bucket),
        dataset=True,
        mode="overwrite_partitions",
        partition_cols=["dt"],
        compression="snappy",
    )
    log.info("%d linhas gravadas em %d arquivo(s)", len(df), len(result["paths"]))
    return result["paths"]
