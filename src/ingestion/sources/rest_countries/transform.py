"""Converte a resposta da Rest Countries v5 em um DataFrame com schema fixo."""

from collections.abc import Sequence

import pandas as pd

from ingestion.sources.rest_countries.config import COLUMNS


def _text(value: str | None) -> str | None:
    """A API usa texto vazio para dizer que não há valor (códigos, sub-região)."""
    value = (value or "").strip() if isinstance(value, str) else value
    return value or None


def _joined(values: Sequence[str | None]) -> str | None:
    """Lista como texto: sem vazios nem repetidos, em ordem alfabética."""
    unique = sorted({value for value in (_text(v) for v in values) if value})
    return ", ".join(unique) or None


def _primary_capital(capitals: list[dict] | None) -> str | None:
    capitals = capitals or []
    primary = [c for c in capitals if (c.get("attributes") or {}).get("primary")]
    chosen = (primary or capitals)[:1]
    return _text(chosen[0].get("name")) if chosen else None


def countries_dataframe(records: Sequence[dict]) -> pd.DataFrame:
    """Uma linha por país ou território."""
    if not records:
        raise ValueError("Rest Countries não devolveu nenhum país")
    rows = []
    for r in records:
        codes = r.get("codes") or {}
        names = r.get("names") or {}
        classification = r.get("classification") or {}
        coordinates = r.get("coordinates") or {}
        rows.append(
            {
                "alpha_3": _text(codes.get("alpha_3")),
                "alpha_2": _text(codes.get("alpha_2")),
                "numeric_code": _text(codes.get("ccn3")),
                "name_common": _text(names.get("common")),
                "name_official": _text(names.get("official")),
                "region": _text(r.get("region")),
                "subregion": _text(r.get("subregion")),
                "population": r.get("population"),
                "area_km2": (r.get("area") or {}).get("kilometers"),
                "capital": _primary_capital(r.get("capitals")),
                "currencies": _joined([c.get("code") for c in r.get("currencies") or []]),
                "languages": _joined([lang.get("name") for lang in r.get("languages") or []]),
                "timezones": _joined(r.get("timezones") or []),
                "un_member": classification.get("un_member"),
                "sovereign": classification.get("sovereign"),
                "disputed": classification.get("disputed"),
                "iso_status": _text(classification.get("iso_status")),
                "latitude": coordinates.get("lat"),
                "longitude": coordinates.get("lng"),
            }
        )
    df = pd.DataFrame(rows).astype(
        {
            "population": "Int64",
            "area_km2": "float64",
            "latitude": "float64",
            "longitude": "float64",
            "un_member": "boolean",
            "sovereign": "boolean",
            "disputed": "boolean",
        }
    )
    return df[[column.name for column in COLUMNS]]
