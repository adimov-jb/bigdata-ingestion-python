from ingestion.source import Column

API_URL = "https://api.restcountries.com/countries/v5"
# Chave do plano gratuito (https://restcountries.com/sign-up). Localmente vem de
# platform/secrets.env (repositório Terraform); na AWS, do Secrets Manager.
API_KEY_ENV = "REST_COUNTRIES_API_KEY"
# Máximo por página no plano gratuito; são cerca de 250 países (3 páginas).
PAGE_SIZE = 100

COLUMNS: tuple[Column, ...] = (
    # ISO 3166-1 alpha-3: chave de ligação com o Banco Mundial. Nulo nos territórios sem
    # código ISO (iso_status = "unassigned", como Abkhazia e Somalilândia).
    Column("alpha_3", "varchar"),
    Column("alpha_2", "varchar"),
    Column("numeric_code", "varchar"),
    Column("name_common", "varchar"),
    Column("name_official", "varchar"),
    Column("region", "varchar"),
    Column("subregion", "varchar"),
    Column("population", "bigint"),
    Column("area_km2", "double"),
    Column("capital", "varchar"),
    # Listas gravadas como texto separado por vírgula, em ordem alfabética.
    Column("currencies", "varchar"),
    Column("languages", "varchar"),
    Column("timezones", "varchar"),
    Column("un_member", "boolean"),
    Column("sovereign", "boolean"),
    Column("disputed", "boolean"),
    # "official", "user_assigned" (código provisório, como UNK do Kosovo) ou "unassigned".
    Column("iso_status", "varchar"),
    Column("latitude", "double"),
    Column("longitude", "double"),
)
