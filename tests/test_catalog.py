from ingestion.catalog import table_statements
from ingestion.sources.open_meteo import SOURCE


def test_open_meteo_table_keeps_existing_schema():
    create, sync = table_statements(SOURCE, "bucket")

    columns = [
        "city varchar",
        "latitude double",
        "longitude double",
        "observed_at timestamp(3)",
        "temperature_2m double",
        "relative_humidity_2m double",
        "precipitation double",
        "wind_speed_10m double",
        "weather_code bigint",
        "ingested_at timestamp(3)",
        "dt varchar",
    ]
    body = create.split("(", 1)[1].split(")\n", 1)[0]
    assert [line.strip().rstrip(",") for line in body.strip().splitlines()] == columns
    assert "hive.bronze.open_meteo_weather_hourly" in create
    assert "external_location = 's3://bucket/open_meteo/weather_hourly/'" in create
    assert "'bronze', 'open_meteo_weather_hourly', 'FULL'" in sync
