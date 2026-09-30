"""Contrato de uma fonte de ingestão.

Cada fonte vive em `ingestion/sources/<nome>/` e expõe um `SOURCE`. O restante
(metadados, gravação, catálogo e CLI) é comum a todas.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class Column:
    name: str
    # Tipo no Hive/Trino, usado no DDL do catálogo local (ex.: varchar, double, timestamp(3)).
    type: str


# Colunas adicionadas pelo pipeline a toda tabela bronze; as fontes não as devolvem.
METADATA_COLUMNS: tuple[Column, ...] = (
    Column("ingested_at", "timestamp(3)"),
    Column("dt", "varchar"),
)


@dataclass(frozen=True)
class Source:
    # Identificador usado no CLI: `ingestion run <name>`.
    name: str
    description: str
    # Prefixo dentro do bucket bronze: <bucket>/<dataset>/dt=YYYY-MM-DD/
    dataset: str
    # Tabela no schema bronze do catálogo.
    table: str
    # Schema de negócio, na ordem das colunas; sem ingested_at e dt.
    columns: tuple[Column, ...]
    # Busca e transforma um dia. Deve devolver exatamente as colunas de `columns`.
    extract: Callable[[date], pd.DataFrame]

    @property
    def bronze_columns(self) -> tuple[Column, ...]:
        return self.columns + METADATA_COLUMNS
