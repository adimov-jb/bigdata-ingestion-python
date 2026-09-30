"""Converte as respostas do Banco Mundial em DataFrames com schema fixo."""

from collections.abc import Sequence

import pandas as pd

from ingestion.sources.world_bank.config import COUNTRY_COLUMNS, INDICATOR_COLUMNS


def _text(value: str | None) -> str | None:
    """A API usa texto vazio para dizer que não há valor e às vezes deixa espaços no fim."""
    value = (value or "").strip()
    return value or None


def _number(value: str | None) -> float | None:
    value = _text(value)
    return float(value) if value is not None else None


def indicators_dataframe(records: Sequence[dict]) -> pd.DataFrame:
    """Formato longo: uma linha por indicador, país (ou agregado) e ano."""
    if not records:
        raise ValueError("Banco Mundial não devolveu nenhum registro de indicador")
    df = pd.DataFrame(
        {
            "indicator_id": [r["indicator"]["id"] for r in records],
            "indicator_name": [_text(r["indicator"]["value"]) for r in records],
            "country_iso3": [_text(r.get("countryiso3code")) for r in records],
            "country_wb_code": [r["country"]["id"] for r in records],
            "country_name": [_text(r["country"]["value"]) for r in records],
            "year": [int(r["date"]) for r in records],
            "value": [r["value"] for r in records],
            "obs_status": [_text(r.get("obs_status")) for r in records],
        }
    )
    df = df.astype({"year": "int64", "value": "float64"})
    return df[[column.name for column in INDICATOR_COLUMNS]]


def countries_dataframe(records: Sequence[dict]) -> pd.DataFrame:
    """Uma linha por país ou agregado, com a classificação do Banco Mundial."""
    if not records:
        raise ValueError("Banco Mundial não devolveu nenhum país")
    df = pd.DataFrame(
        {
            "iso3": [r["id"] for r in records],
            "iso2": [_text(r.get("iso2Code")) for r in records],
            "name": [_text(r["name"]) for r in records],
            "region": [_text(r["region"]["value"]) for r in records],
            "income_level": [_text(r["incomeLevel"]["value"]) for r in records],
            "lending_type": [_text(r["lendingType"]["value"]) for r in records],
            "capital_city": [_text(r.get("capitalCity")) for r in records],
            "latitude": [_number(r.get("latitude")) for r in records],
            "longitude": [_number(r.get("longitude")) for r in records],
            "is_aggregate": [_text(r["region"]["value"]) == "Aggregates" for r in records],
        }
    )
    df = df.astype({"latitude": "float64", "longitude": "float64", "is_aggregate": "bool"})
    return df[[column.name for column in COUNTRY_COLUMNS]]
