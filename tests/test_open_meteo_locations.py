from datetime import UTC, date, datetime

import pytest

from ingestion.catalog import table_statements
from ingestion.pipeline import with_metadata
from ingestion.sources.open_meteo import LOCATIONS_SOURCE
from ingestion.sources.open_meteo.config import LOCATIONS, Location
from ingestion.sources.open_meteo.transform import locations_dataframe

DAY = date(2026, 9, 29)


def test_one_row_per_location(locations):
    df = locations_dataframe(locations)

    assert list(df.columns) == [column.name for column in LOCATIONS_SOURCE.columns]
    assert df.to_dict("records") == [
        {
            "city": "Cidade A",
            "state": "AA",
            "region": "Norte",
            "latitude": -10.0,
            "longitude": -40.0,
        },
        {"city": "Cidade B", "state": "BB", "region": "Sul", "latitude": -20.0, "longitude": -50.0},
    ]


def test_snapshot_passes_the_pipeline_schema_check():
    df = with_metadata(
        LOCATIONS_SOURCE.extract(DAY), LOCATIONS_SOURCE, DAY, datetime(2026, 9, 30, tzinfo=UTC)
    )

    assert len(df) == len(LOCATIONS)
    assert (df["dt"] == "2026-09-29").all()


def test_monitored_cities_are_unique():
    names = [location.name for location in LOCATIONS]

    assert len(names) == len(set(names))


def test_invalid_region_is_rejected():
    with pytest.raises(ValueError, match="região inválida"):
        Location("Cidade X", "XX", "Leste", 0.0, 0.0)


def test_locations_table_ddl():
    create, _ = table_statements(LOCATIONS_SOURCE, "bucket")

    assert "hive.bronze.open_meteo_locations" in create
    assert "external_location = 's3://bucket/open_meteo/locations/'" in create
    assert "region varchar" in create
