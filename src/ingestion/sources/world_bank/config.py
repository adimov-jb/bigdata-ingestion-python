from ingestion.source import Column

API_URL = "https://api.worldbank.org/v2"
# Uma página cobre um indicador inteiro (≈ 7 mil linhas); o cliente pagina se passar disso.
PER_PAGE = 20000

# Indicadores ingeridos. A bronze guarda o nome oficial vindo da API; o dbt decide como
# modelar cada um (seed world_bank_indicators), e um teste acusa indicador sem mapeamento.
INDICATORS: tuple[str, ...] = (
    "NY.GDP.MKTP.CD",  # PIB (US$ correntes)
    "FP.CPI.TOTL.ZG",  # Inflação, preços ao consumidor (% ao ano)
    "SP.DYN.LE00.IN",  # Expectativa de vida ao nascer (anos)
    "SI.POV.DDAY",  # Pobreza: % da população abaixo da linha internacional
    "SP.POP.TOTL",  # População total
)

# Série histórica desde este ano até o ano da data processada.
START_YEAR = 2000

INDICATOR_COLUMNS: tuple[Column, ...] = (
    Column("indicator_id", "varchar"),
    Column("indicator_name", "varchar"),
    # ISO alpha-3. Vem vazio na API para alguns agregados (faixas de renda): gravado como nulo.
    Column("country_iso3", "varchar"),
    # Código interno do Banco Mundial (ISO alpha-2 nos países, códigos próprios nos agregados).
    Column("country_wb_code", "varchar"),
    Column("country_name", "varchar"),
    Column("year", "bigint"),
    # Nulo quando o Banco Mundial não tem o dado daquele país e ano.
    Column("value", "double"),
    Column("obs_status", "varchar"),
)

COUNTRY_COLUMNS: tuple[Column, ...] = (
    Column("iso3", "varchar"),
    Column("iso2", "varchar"),
    Column("name", "varchar"),
    Column("region", "varchar"),
    Column("income_level", "varchar"),
    Column("lending_type", "varchar"),
    Column("capital_city", "varchar"),
    Column("latitude", "double"),
    Column("longitude", "double"),
    # Regiões e faixas de renda (region = "Aggregates"), que não são países.
    Column("is_aggregate", "boolean"),
)
