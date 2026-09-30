from dataclasses import dataclass

from ingestion.source import Column


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float


# Capitais monitoradas. Para incluir uma cidade, basta adicioná-la aqui.
LOCATIONS: tuple[Location, ...] = (
    Location("Sao Paulo", -23.55, -46.63),
    Location("Rio de Janeiro", -22.91, -43.17),
    Location("Brasilia", -15.78, -47.93),
    Location("Belo Horizonte", -19.92, -43.94),
    Location("Salvador", -12.97, -38.50),
    Location("Fortaleza", -3.72, -38.54),
    Location("Recife", -8.05, -34.88),
    Location("Porto Alegre", -30.03, -51.23),
    Location("Curitiba", -25.43, -49.27),
    Location("Manaus", -3.12, -60.02),
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

# Schema de negócio na bronze; ingested_at e dt são adicionados pelo pipeline.
COLUMNS: tuple[Column, ...] = (
    Column("city", "varchar"),
    Column("latitude", "double"),
    Column("longitude", "double"),
    Column("observed_at", "timestamp(3)"),
    *(Column(name, "double") for name in FLOAT_VARIABLES),
    *(Column(name, "bigint") for name in INT_VARIABLES),
)
