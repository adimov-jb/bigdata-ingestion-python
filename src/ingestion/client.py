"""Cliente HTTP da API Open-Meteo (gratuita, sem chave)."""

import logging
from collections.abc import Sequence
from datetime import UTC, date, datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ingestion.config import HOURLY_VARIABLES, Location

log = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# A API de arquivo (reanálise ERA5) tem alguns dias de atraso; datas recentes
# vêm da API de previsão, que também devolve dias passados.
FORECAST_MAX_PAST_DAYS = 60
REQUEST_TIMEOUT_SECONDS = 30


def build_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def endpoint_for(day: date, today: date) -> str:
    if day > today:
        raise ValueError(f"Data futura não é permitida: {day}")
    if (today - day).days <= FORECAST_MAX_PAST_DAYS:
        return FORECAST_URL
    return ARCHIVE_URL


def fetch_hourly(
    day: date,
    locations: Sequence[Location],
    session: requests.Session | None = None,
    today: date | None = None,
) -> list[dict]:
    """Busca as variáveis horárias de um dia (UTC) para todas as localidades em uma chamada."""
    session = session or build_session()
    today = today or datetime.now(UTC).date()
    url = endpoint_for(day, today)

    params = {
        "latitude": ",".join(str(loc.latitude) for loc in locations),
        "longitude": ",".join(str(loc.longitude) for loc in locations),
        "hourly": ",".join(HOURLY_VARIABLES),
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
        "timezone": "GMT",
    }
    log.info("GET %s para %s (%d localidades)", url, day, len(locations))
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    payload = response.json()
    # Com uma única localidade a API devolve um objeto; com várias, uma lista na mesma ordem.
    if isinstance(payload, dict):
        payload = [payload]
    if len(payload) != len(locations):
        raise ValueError(f"API devolveu {len(payload)} localidades, esperado {len(locations)}")
    return payload
