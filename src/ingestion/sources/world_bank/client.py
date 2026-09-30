"""Cliente HTTP da API do Banco Mundial (v2, sem chave)."""

import logging

import requests

from ingestion.http import REQUEST_TIMEOUT_SECONDS, build_session
from ingestion.sources.world_bank.config import API_URL, PER_PAGE

log = logging.getLogger(__name__)


def get_all_pages(path: str, params: dict, session: requests.Session | None = None) -> list[dict]:
    """Junta todas as páginas de um endpoint. A API devolve [meta, registros]."""
    session = session or build_session()
    records: list[dict] = []
    page = 1
    while True:
        response = session.get(
            f"{API_URL}/{path}",
            params={**params, "format": "json", "per_page": PER_PAGE, "page": page},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        # Erros vêm com HTTP 200 e formato [{"message": [...]}]. Sem esta checagem,
        # a mensagem de erro seria tratada como uma página vazia.
        if not (isinstance(payload, list) and len(payload) == 2 and "pages" in payload[0]):
            raise ValueError(f"Resposta inesperada do Banco Mundial em {path}: {payload!r:.300}")
        meta, data = payload
        records.extend(data or [])
        if page >= int(meta["pages"]):
            break
        page += 1
    log.info("GET %s: %d registros em %d página(s)", path, len(records), page)
    return records


def fetch_indicator(
    indicator: str, start_year: int, end_year: int, session: requests.Session | None = None
) -> list[dict]:
    return get_all_pages(
        f"country/all/indicator/{indicator}", {"date": f"{start_year}:{end_year}"}, session
    )


def fetch_countries(session: requests.Session | None = None) -> list[dict]:
    return get_all_pages("country", {}, session)
