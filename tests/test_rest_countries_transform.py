from datetime import UTC, date, datetime

import pandas as pd
import pytest

from ingestion.pipeline import with_metadata
from ingestion.sources.rest_countries import SOURCE
from ingestion.sources.rest_countries.transform import countries_dataframe

# Recortes de respostas reais da v5 (campos não usados removidos).
AFGHANISTAN = {
    "names": {"common": "Afghanistan", "official": "Islamic Republic of Afghanistan"},
    "codes": {"alpha_2": "AF", "alpha_3": "AFG", "ccn3": "004"},
    "region": "Asia",
    "subregion": "Southern Asia",
    "population": 43844000,
    "area": {"kilometers": 652230, "miles": 251827.3},
    "capitals": [
        {
            "attributes": {"primary": True},
            "coordinates": {"lat": 34.52, "lng": 69.18},
            "name": "Kabul",
        }
    ],
    "currencies": [{"code": "AFN", "name": "Afghan afghani", "symbol": "؋"}],
    "languages": [
        {"iso639_3": "pus", "name": "Pashto"},
        {"iso639_3": "prs", "name": "Dari"},
        {"iso639_3": "tuk", "name": "Turkmen"},
    ],
    "timezones": ["UTC+04:30"],
    "classification": {
        "disputed": False,
        "iso_status": "official",
        "sovereign": True,
        "un_member": True,
    },
    "coordinates": {"lat": 33, "lng": 65},
}

# Território sem código ISO: códigos vêm como texto vazio.
ABKHAZIA = {
    "names": {"common": "Abkhazia", "official": "Republic of Abkhazia"},
    "codes": {"alpha_2": "", "alpha_3": "", "ccn3": ""},
    "region": "Asia",
    "subregion": "Western Asia",
    "population": 244236,
    "area": {"kilometers": 8665},
    "capitals": [{"attributes": {"primary": True}, "name": "Sukhumi"}],
    "currencies": [],
    "languages": [],
    "timezones": [],
    "classification": {"iso_status": "unassigned", "sovereign": False, "un_member": False},
    "coordinates": {"lat": 43, "lng": 41},
}


def test_country_fields():
    row = countries_dataframe([AFGHANISTAN]).iloc[0]

    assert row["alpha_3"] == "AFG"
    assert row["capital"] == "Kabul"
    assert row["currencies"] == "AFN"
    # Ordem alfabética, para a coluna não mudar só porque a API mudou a ordem da lista.
    assert row["languages"] == "Dari, Pashto, Turkmen"
    assert row["population"] == 43844000
    assert row["area_km2"] == 652230.0
    assert bool(row["un_member"]) is True
    assert row["iso_status"] == "official"


def test_territory_without_iso_code_keeps_nulls():
    df = countries_dataframe([AFGHANISTAN, ABKHAZIA])
    row = df.iloc[1]

    assert list(df.columns) == [column.name for column in SOURCE.columns]
    assert pd.isna(row["alpha_3"])
    assert pd.isna(row["numeric_code"])
    assert pd.isna(row["currencies"])
    assert pd.isna(row["disputed"])
    assert row["iso_status"] == "unassigned"


def test_capital_prefers_the_primary_one():
    country = {
        **AFGHANISTAN,
        "capitals": [
            {"attributes": {"primary": False}, "name": "Secundária"},
            {"attributes": {"primary": True}, "name": "Principal"},
        ],
    }

    assert countries_dataframe([country]).iloc[0]["capital"] == "Principal"


def test_snapshot_passes_the_pipeline_schema_check():
    df = countries_dataframe([AFGHANISTAN, ABKHAZIA])

    result = with_metadata(df, SOURCE, date(2026, 9, 29), datetime(2026, 9, 30, tzinfo=UTC))

    assert len(result) == 2


def test_empty_response_fails():
    with pytest.raises(ValueError):
        countries_dataframe([])
