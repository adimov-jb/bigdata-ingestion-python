"""Cliente HTTP da Rest Countries v5 (exige chave de API)."""

import logging
import os

import requests

from ingestion.http import REQUEST_TIMEOUT_SECONDS, build_session
from ingestion.sources.rest_countries.config import API_KEY_ENV, API_URL, PAGE_SIZE

log = logging.getLogger(__name__)


def api_key() -> str:
    key = os.getenv(API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(
            f"{API_KEY_ENV} não definida. Localmente, preencha platform/secrets.env no "
            "repositório Terraform (modelo em platform/secrets.env.example)."
        )
    return key


def fetch_countries(session: requests.Session | None = None, key: str | None = None) -> list[dict]:
    """Todos os países, página a página (limit/offset), até meta.more ser falso."""
    session = session or build_session()
    headers = {"Authorization": f"Bearer {key or api_key()}"}
    countries: list[dict] = []
    offset = 0
    while True:
        response = session.get(
            API_URL,
            params={"limit": PAGE_SIZE, "offset": offset},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        payload = response.json() if response.content else {}
        data = payload.get("data") if isinstance(payload, dict) else None
        # A API também responde erros (inclusive versão descontinuada) com envelope
        # {"data": null, "errors": [...]}, às vezes com HTTP 200: confere o conteúdo.
        if not response.ok or not isinstance(data, dict) or "objects" not in data:
            errors = payload.get("errors") if isinstance(payload, dict) else payload
            raise RuntimeError(
                f"Rest Countries respondeu HTTP {response.status_code}: {errors!r:.300}"
            )
        countries.extend(data["objects"])
        meta = data.get("meta") or {}
        if not meta.get("more"):
            break
        offset += len(data["objects"])
    log.info("GET %s: %d países", API_URL, len(countries))
    return countries
