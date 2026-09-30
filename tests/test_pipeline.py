from datetime import UTC, date, datetime

import awswrangler as wr
import pandas as pd
import pytest
from conftest import BUCKET, fake_source

from ingestion.pipeline import run_source, with_metadata
from ingestion.writer import dataset_path

DAY = date(2026, 9, 29)
INGESTED_AT = datetime(2026, 9, 30, 3, 0, tzinfo=UTC)


def test_metadata_columns_are_appended_in_schema_order():
    source = fake_source()

    df = with_metadata(source.extract(DAY), source, DAY, INGESTED_AT)

    assert list(df.columns) == ["id", "value", "ingested_at", "dt"]
    assert (df["dt"] == "2026-09-29").all()
    assert df["ingested_at"].dt.tz is None
    assert (df["ingested_at"] == pd.Timestamp("2026-09-30 03:00")).all()


def test_missing_column_raises():
    source = fake_source()

    with pytest.raises(ValueError, match="faltando=\\['value'\\]"):
        with_metadata(pd.DataFrame({"id": [1]}), source, DAY, INGESTED_AT)


def test_unexpected_column_raises():
    source = fake_source()
    df = pd.DataFrame({"id": [1], "value": [1.0], "surprise": ["x"]})

    with pytest.raises(ValueError, match="sobrando=\\['surprise'\\]"):
        with_metadata(df, source, DAY, INGESTED_AT)


def test_empty_frame_raises():
    source = fake_source()

    with pytest.raises(ValueError, match="nenhuma linha"):
        with_metadata(pd.DataFrame({"id": [], "value": []}), source, DAY, INGESTED_AT)


def test_run_source_writes_to_its_dataset(s3, settings):
    source = fake_source()

    run_source(source, DAY, settings, ingested_at=INGESTED_AT)

    result = wr.s3.read_parquet(dataset_path(BUCKET, source.dataset), dataset=True)
    assert sorted(result["id"]) == [1, 2]
