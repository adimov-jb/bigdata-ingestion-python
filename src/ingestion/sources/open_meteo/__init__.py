"""Open-Meteo: tempo horário das capitais brasileiras (API gratuita, sem chave)."""

from datetime import date

import pandas as pd

from ingestion.source import Source
from ingestion.sources.open_meteo.client import fetch_hourly
from ingestion.sources.open_meteo.config import COLUMNS, LOCATIONS
from ingestion.sources.open_meteo.transform import to_dataframe


def extract(day: date) -> pd.DataFrame:
    return to_dataframe(fetch_hourly(day, LOCATIONS), LOCATIONS, day)


SOURCE = Source(
    name="open_meteo",
    description="Tempo horário das capitais brasileiras (Open-Meteo)",
    dataset="open_meteo/weather_hourly",
    table="open_meteo_weather_hourly",
    columns=COLUMNS,
    extract=extract,
)
