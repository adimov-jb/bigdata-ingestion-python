from datetime import UTC, date, datetime

import awswrangler as wr
from conftest import BUCKET, fake_source

from ingestion.pipeline import with_metadata
from ingestion.writer import dataset_path, write_bronze

SOURCE = fake_source()


def frame(day):
    return with_metadata(SOURCE.extract(day), SOURCE, day, datetime(2026, 9, 30, tzinfo=UTC))


def test_writes_partitioned_parquet(s3):
    paths = write_bronze(frame(date(2026, 9, 29)), BUCKET, SOURCE.dataset)

    assert paths
    assert all("/fake/items/dt=2026-09-29/" in p for p in paths)
    assert all(p.endswith(".snappy.parquet") for p in paths)


def test_rerun_same_day_is_idempotent(s3):
    df = frame(date(2026, 9, 29))

    write_bronze(df, BUCKET, SOURCE.dataset)
    write_bronze(df, BUCKET, SOURCE.dataset)

    assert len(wr.s3.read_parquet(dataset_path(BUCKET, SOURCE.dataset), dataset=True)) == len(df)


def test_other_days_are_preserved(s3):
    write_bronze(frame(date(2026, 9, 28)), BUCKET, SOURCE.dataset)
    write_bronze(frame(date(2026, 9, 29)), BUCKET, SOURCE.dataset)

    result = wr.s3.read_parquet(dataset_path(BUCKET, SOURCE.dataset), dataset=True)

    assert set(result["dt"].astype(str)) == {"2026-09-28", "2026-09-29"}


def test_sources_do_not_share_datasets(s3):
    other = fake_source("other")

    write_bronze(frame(date(2026, 9, 29)), BUCKET, SOURCE.dataset)
    write_bronze(frame(date(2026, 9, 29)), BUCKET, other.dataset)

    assert len(wr.s3.read_parquet(dataset_path(BUCKET, SOURCE.dataset), dataset=True)) == 2
    assert len(wr.s3.read_parquet(dataset_path(BUCKET, other.dataset), dataset=True)) == 2
