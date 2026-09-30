"""Gravação na camada bronze: Parquet particionado por dt."""

import logging

import awswrangler as wr
import pandas as pd

log = logging.getLogger(__name__)


def dataset_path(bucket: str, dataset: str) -> str:
    return f"s3://{bucket}/{dataset}/"


def write_bronze(
    df: pd.DataFrame,
    bucket: str,
    dataset: str,
    endpoint_url: str | None = None,
) -> list[str]:
    """Substitui só as partições presentes no DataFrame: reexecutar um dia é idempotente."""
    if endpoint_url:
        wr.config.s3_endpoint_url = endpoint_url

    result = wr.s3.to_parquet(
        df=df,
        path=dataset_path(bucket, dataset),
        dataset=True,
        mode="overwrite_partitions",
        partition_cols=["dt"],
        compression="snappy",
    )
    log.info("%s: %d linhas gravadas em %d arquivo(s)", dataset, len(df), len(result["paths"]))
    return result["paths"]
