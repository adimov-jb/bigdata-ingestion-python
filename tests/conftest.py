import boto3
import pandas as pd
import pytest
from moto import mock_aws

from ingestion.settings import Settings
from ingestion.source import Column, Source
from ingestion.sources.open_meteo.config import HOURLY_VARIABLES, Location

LOCATIONS = (
    Location("Cidade A", -10.0, -40.0),
    Location("Cidade B", -20.0, -50.0),
)

BUCKET = "bronze-test"


def api_item(hours: int = 24, day: str = "2026-09-29") -> dict:
    hourly = {"time": [f"{day}T{h:02d}:00" for h in range(hours)]}
    for variable in HOURLY_VARIABLES:
        hourly[variable] = [float(h) for h in range(hours)]
    hourly["weather_code"] = [3] * hours
    return {"latitude": 0.0, "longitude": 0.0, "hourly": hourly}


def fake_source(name: str = "fake", extract=None) -> Source:
    """Fonte mínima para testar o núcleo sem depender de uma API."""
    return Source(
        name=name,
        description="Fonte de teste",
        dataset=f"{name}/items",
        table=f"{name}_items",
        columns=(Column("id", "bigint"), Column("value", "double")),
        extract=extract or (lambda day: pd.DataFrame({"value": [1.5, 2.5], "id": [1, 2]})),
    )


@pytest.fixture
def locations():
    return LOCATIONS


@pytest.fixture
def payload():
    return [api_item(), api_item()]


@pytest.fixture
def settings():
    return Settings(
        bronze_bucket=BUCKET, aws_endpoint_url=None, trino_host="trino", trino_port=8080
    )


@pytest.fixture
def s3(monkeypatch):
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        boto3.client("s3").create_bucket(Bucket=BUCKET)
        yield
