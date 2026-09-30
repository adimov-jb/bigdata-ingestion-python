"""Registro das fontes de ingestão.

Para adicionar uma fonte, crie `sources/<nome>/__init__.py` expondo um `SOURCE`
e inclua-o em `_ALL` abaixo.
"""

from ingestion.source import Source
from ingestion.sources import open_meteo

_ALL: tuple[Source, ...] = (open_meteo.SOURCE,)

SOURCES: dict[str, Source] = {source.name: source for source in _ALL}

if len(SOURCES) != len(_ALL):
    raise RuntimeError("Há fontes com nome duplicado em ingestion.sources")
