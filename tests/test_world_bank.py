from datetime import UTC, date, datetime

import pytest
import requests
import responses

from ingestion.pipeline import with_metadata
from ingestion.sources.world_bank import COUNTRIES_SOURCE, INDICATORS_SOURCE
from ingestion.sources.world_bank.client import API_URL, fetch_countries, fetch_indicator
from ingestion.sources.world_bank.transform import countries_dataframe, indicators_dataframe

INDICATOR_URL = f"{API_URL}/country/all/indicator/SP.POP.TOTL"


def indicator_record(iso3="BRA", code="BR", name="Brazil", year="2024", value=211.0):
    return {
        "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
        "country": {"id": code, "value": name},
        "countryiso3code": iso3,
        "date": year,
        "value": value,
        "unit": "",
        "obs_status": "",
        "decimal": 0,
    }


def country_record(iso3="BRA", iso2="BR", name="Brazil", region="Latin America & Caribbean "):
    return {
        "id": iso3,
        "iso2Code": iso2,
        "name": name,
        "region": {"id": "LCN", "iso2code": "ZJ", "value": region},
        "incomeLevel": {"id": "UMC", "iso2code": "XT", "value": "Upper middle income"},
        "lendingType": {"id": "IBD", "iso2code": "XF", "value": "IBRD"},
        "capitalCity": "Brasilia",
        "longitude": "-47.9292",
        "latitude": "-15.7801",
    }


def page(records, number=1, pages=1):
    return [{"page": number, "pages": pages, "per_page": 20000, "total": 0}, records]


@responses.activate
def test_indicator_pages_are_joined():
    responses.get(INDICATOR_URL, json=page([indicator_record(year="2024")], 1, 2))
    responses.get(INDICATOR_URL, json=page([indicator_record(year="2023")], 2, 2))

    records = fetch_indicator("SP.POP.TOTL", 2000, 2026, session=requests.Session())

    assert [r["date"] for r in records] == ["2024", "2023"]
    assert responses.calls[0].request.params["date"] == "2000:2026"
    assert responses.calls[1].request.params["page"] == "2"


@responses.activate
def test_error_with_http_200_is_not_treated_as_empty_page():
    error = [{"message": [{"id": "120", "key": "Invalid value", "value": "not valid"}]}]
    responses.get(INDICATOR_URL, json=error)

    with pytest.raises(ValueError, match="Resposta inesperada"):
        fetch_indicator("SP.POP.TOTL", 2000, 2026, session=requests.Session())


@responses.activate
def test_countries_endpoint():
    responses.get(f"{API_URL}/country", json=page([country_record()]))

    assert len(fetch_countries(session=requests.Session())) == 1


def test_indicator_nulls_and_empty_codes_become_null():
    df = indicators_dataframe(
        [
            indicator_record(value=None),
            indicator_record(iso3="", code="XD", name="High income", value=1.0),
        ]
    )

    assert list(df.columns) == [column.name for column in INDICATORS_SOURCE.columns]
    assert df["value"].isna().tolist() == [True, False]
    assert df["country_iso3"].isna().tolist() == [False, True]
    assert df["year"].dtype == "int64"


def test_aggregates_are_flagged_and_text_is_trimmed():
    df = countries_dataframe(
        [country_record(), country_record(iso3="WLD", iso2="1W", name="World", region="Aggregates")]
    )

    assert list(df.columns) == [column.name for column in COUNTRIES_SOURCE.columns]
    assert df["is_aggregate"].tolist() == [False, True]
    assert df.loc[0, "region"] == "Latin America & Caribbean"
    assert df.loc[0, "latitude"] == pytest.approx(-15.7801)


def test_snapshots_pass_the_pipeline_schema_check():
    day = date(2026, 9, 29)
    ingested = datetime(2026, 9, 30, tzinfo=UTC)

    indicators = indicators_dataframe([indicator_record()])
    countries = countries_dataframe([country_record()])

    assert len(with_metadata(indicators, INDICATORS_SOURCE, day, ingested)) == 1
    assert len(with_metadata(countries, COUNTRIES_SOURCE, day, ingested)) == 1


def test_empty_responses_fail():
    with pytest.raises(ValueError):
        indicators_dataframe([])
    with pytest.raises(ValueError):
        countries_dataframe([])
