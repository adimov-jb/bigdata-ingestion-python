from datetime import date

import pandas as pd
import pytest

from ingestion.sources.open_meteo import SOURCE
from ingestion.sources.open_meteo.transform import to_dataframe

DAY = date(2026, 9, 29)


def test_one_row_per_city_and_hour(payload, locations):
    df = to_dataframe(payload, locations, DAY)

    assert list(df.columns) == [column.name for column in SOURCE.columns]
    assert len(df) == 48
    assert set(df["city"]) == {"Cidade A", "Cidade B"}


def test_types_are_stable(payload, locations):
    df = to_dataframe(payload, locations, DAY)

    assert pd.api.types.is_datetime64_dtype(df["observed_at"])
    assert df["observed_at"].dt.tz is None
    assert df["temperature_2m"].dtype == "float64"
    assert str(df["weather_code"].dtype) == "Int64"


def test_null_values_are_kept(payload, locations):
    payload[0]["hourly"]["temperature_2m"][0] = None
    payload[0]["hourly"]["weather_code"][0] = None

    df = to_dataframe(payload, locations, DAY)

    assert df["temperature_2m"].isna().sum() == 1
    assert df["weather_code"].isna().sum() == 1


def test_missing_variable_raises(payload, locations):
    del payload[1]["hourly"]["precipitation"]

    with pytest.raises(ValueError, match="precipitation"):
        to_dataframe(payload, locations, DAY)
