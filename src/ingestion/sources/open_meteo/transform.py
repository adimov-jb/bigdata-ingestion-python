"""Converte a resposta da API em um DataFrame com schema fixo."""

from collections.abc import Sequence
from datetime import date

import pandas as pd

from ingestion.sources.open_meteo.config import (
    COLUMNS,
    FLOAT_VARIABLES,
    HOURLY_VARIABLES,
    INT_VARIABLES,
    LOCATION_COLUMNS,
    Location,
)


def locations_dataframe(locations: Sequence[Location]) -> pd.DataFrame:
    """Uma linha por localidade monitorada."""
    df = pd.DataFrame(
        {
            "city": [loc.name for loc in locations],
            "state": [loc.state for loc in locations],
            "region": [loc.region for loc in locations],
            "latitude": [float(loc.latitude) for loc in locations],
            "longitude": [float(loc.longitude) for loc in locations],
        }
    )
    return df[[column.name for column in LOCATION_COLUMNS]]


def to_dataframe(payload: Sequence[dict], locations: Sequence[Location], day: date) -> pd.DataFrame:
    """Uma linha por cidade e hora. Timestamps em UTC, sem timezone."""
    frames = []
    for location, item in zip(locations, payload, strict=True):
        hourly = item.get("hourly") or {}
        missing = [key for key in ("time", *HOURLY_VARIABLES) if key not in hourly]
        if missing:
            raise ValueError(f"{location.name}: variáveis ausentes na resposta: {missing}")

        frame = pd.DataFrame({key: hourly[key] for key in ("time", *HOURLY_VARIABLES)})
        frame["city"] = location.name
        frame["latitude"] = location.latitude
        frame["longitude"] = location.longitude
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        raise ValueError(f"API não devolveu dados para {day}")

    df["observed_at"] = pd.to_datetime(df.pop("time"))
    df = df.astype({col: "float64" for col in FLOAT_VARIABLES})
    df = df.astype({col: "Int64" for col in INT_VARIABLES})
    return df[[column.name for column in COLUMNS]]
