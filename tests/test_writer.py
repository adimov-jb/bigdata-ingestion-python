from datetime import UTC, date, datetime

import awswrangler as wr
import boto3
import pytest
from moto import mock_aws

from ingestion.transform import to_dataframe
from ingestion.writer import dataset_path, write_bronze

BUCKET = "bronze-test"


@pytest.fixture
def s3(monkeypatch):
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        boto3.client("s3").create_bucket(Bucket=BUCKET)
        yield


def frame(payload, locations, day):
    return to_dataframe(payload, locations, day, datetime(2026, 9, 30, tzinfo=UTC))


def test_writes_partitioned_parquet(s3, payload, locations):
    paths = write_bronze(frame(payload, locations, date(2026, 9, 29)), BUCKET)

    assert paths
    assert all("/open_meteo/weather_hourly/dt=2026-09-29/" in p for p in paths)
    assert all(p.endswith(".snappy.parquet") for p in paths)


def test_rerun_same_day_is_idempotent(s3, payload, locations):
    df = frame(payload, locations, date(2026, 9, 29))

    write_bronze(df, BUCKET)
    write_bronze(df, BUCKET)

    assert len(wr.s3.read_parquet(dataset_path(BUCKET), dataset=True)) == len(df)


def test_other_days_are_preserved(s3, payload, locations):
    write_bronze(frame(payload, locations, date(2026, 9, 28)), BUCKET)
    write_bronze(frame(payload, locations, date(2026, 9, 29)), BUCKET)

    result = wr.s3.read_parquet(dataset_path(BUCKET), dataset=True)

    assert set(result["dt"].astype(str)) == {"2026-09-28", "2026-09-29"}
