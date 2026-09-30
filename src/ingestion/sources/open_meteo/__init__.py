"""Open-Meteo: tempo horário das capitais brasileiras (API gratuita, sem chave)."""

from datetime import date

import pandas as pd

from ingestion.source import Source
from ingestion.sources.open_meteo.client import fetch_hourly
from ingestion.sources.open_meteo.config import COLUMNS, LOCATION_COLUMNS, LOCATIONS
from ingestion.sources.open_meteo.transform import locations_dataframe, to_dataframe


def extract(day: date) -> pd.DataFrame:
    return to_dataframe(fetch_hourly(day, LOCATIONS), LOCATIONS, day)


def extract_locations(day: date) -> pd.DataFrame:
    # Não chama a API: grava o snapshot da configuração na partição do dia.
    return locations_dataframe(LOCATIONS)


SOURCE = Source(
    name="open_meteo",
    description="Tempo horário das capitais brasileiras (Open-Meteo)",
    dataset="open_meteo/weather_hourly",
    table="open_meteo_weather_hourly",
    columns=COLUMNS,
    extract=extract,
)

LOCATIONS_SOURCE = Source(
    name="open_meteo_locations",
    description="Cidades monitoradas, com UF, região e coordenadas (snapshot diário)",
    dataset="open_meteo/locations",
    table="open_meteo_locations",
    columns=LOCATION_COLUMNS,
    extract=extract_locations,
)
