"""Banco Mundial: indicadores socioeconômicos por país e ano (API v2, sem chave)."""

from datetime import date

import pandas as pd

from ingestion.http import build_session
from ingestion.source import Source
from ingestion.sources.world_bank.client import fetch_countries, fetch_indicator
from ingestion.sources.world_bank.config import (
    COUNTRY_COLUMNS,
    INDICATOR_COLUMNS,
    INDICATORS,
    START_YEAR,
)
from ingestion.sources.world_bank.transform import countries_dataframe, indicators_dataframe


def extract_indicators(day: date) -> pd.DataFrame:
    # Snapshot da série inteira: o Banco Mundial revisa anos passados, então cada partição
    # guarda a versão publicada naquele dia, e o dbt usa a mais recente.
    session = build_session()
    records = []
    for indicator in INDICATORS:
        records.extend(fetch_indicator(indicator, START_YEAR, day.year, session))
    return indicators_dataframe(records)


def extract_countries(day: date) -> pd.DataFrame:
    return countries_dataframe(fetch_countries())


INDICATORS_SOURCE = Source(
    name="world_bank_indicators",
    description="Indicadores do Banco Mundial por país e ano (PIB, inflação, vida, pobreza)",
    dataset="world_bank/indicators",
    table="world_bank_indicators",
    columns=INDICATOR_COLUMNS,
    extract=extract_indicators,
)

COUNTRIES_SOURCE = Source(
    name="world_bank_countries",
    description="Países e agregados do Banco Mundial, com região e faixa de renda",
    dataset="world_bank/countries",
    table="world_bank_countries",
    columns=COUNTRY_COLUMNS,
    extract=extract_countries,
)
