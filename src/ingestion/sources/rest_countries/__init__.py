"""Rest Countries v5: países e territórios, com população, área, moedas, idiomas e fusos."""

from datetime import date

import pandas as pd

from ingestion.source import Source
from ingestion.sources.rest_countries.client import fetch_countries
from ingestion.sources.rest_countries.config import COLUMNS
from ingestion.sources.rest_countries.transform import countries_dataframe


def extract(day: date) -> pd.DataFrame:
    # Snapshot: a API só tem a situação atual, gravada na partição do dia processado.
    return countries_dataframe(fetch_countries())


SOURCE = Source(
    name="rest_countries",
    description="Países e territórios (Rest Countries v5): população, área, moedas, idiomas",
    dataset="rest_countries/countries",
    table="rest_countries",
    columns=COLUMNS,
    extract=extract,
)
