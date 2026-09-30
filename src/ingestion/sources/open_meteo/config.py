from dataclasses import dataclass

from ingestion.source import Column

# Regiões aceitas pelo teste accepted_values da dim_city no dbt.
REGIONS: frozenset[str] = frozenset({"Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"})


@dataclass(frozen=True)
class Location:
    name: str
    state: str
    region: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise ValueError(f"{self.name}: região inválida {self.region!r}")


# Capitais monitoradas: fonte única da lista de cidades. A fonte open_meteo_locations
# grava esta lista na bronze, e o dbt monta a dim_city a partir dela.
LOCATIONS: tuple[Location, ...] = (
    Location("Sao Paulo", "SP", "Sudeste", -23.55, -46.63),
    Location("Rio de Janeiro", "RJ", "Sudeste", -22.91, -43.17),
    Location("Brasilia", "DF", "Centro-Oeste", -15.78, -47.93),
    Location("Belo Horizonte", "MG", "Sudeste", -19.92, -43.94),
    Location("Salvador", "BA", "Nordeste", -12.97, -38.50),
    Location("Fortaleza", "CE", "Nordeste", -3.72, -38.54),
    Location("Recife", "PE", "Nordeste", -8.05, -34.88),
    Location("Porto Alegre", "RS", "Sul", -30.03, -51.23),
    Location("Curitiba", "PR", "Sul", -25.43, -49.27),
    Location("Manaus", "AM", "Norte", -3.12, -60.02),
)

# Variáveis horárias pedidas à API; viram colunas na bronze.
FLOAT_VARIABLES: tuple[str, ...] = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
)
INT_VARIABLES: tuple[str, ...] = ("weather_code",)
HOURLY_VARIABLES: tuple[str, ...] = FLOAT_VARIABLES + INT_VARIABLES

# Schemas de negócio na bronze; ingested_at e dt são adicionados pelo pipeline.
LOCATION_COLUMNS: tuple[Column, ...] = (
    Column("city", "varchar"),
    Column("state", "varchar"),
    Column("region", "varchar"),
    Column("latitude", "double"),
    Column("longitude", "double"),
)

COLUMNS: tuple[Column, ...] = (
    Column("city", "varchar"),
    Column("latitude", "double"),
    Column("longitude", "double"),
    Column("observed_at", "timestamp(3)"),
    *(Column(name, "double") for name in FLOAT_VARIABLES),
    *(Column(name, "bigint") for name in INT_VARIABLES),
)
