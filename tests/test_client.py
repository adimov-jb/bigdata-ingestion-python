from datetime import date

import pytest
import requests
import responses
from conftest import api_item
from responses import matchers

from ingestion.client import ARCHIVE_URL, FORECAST_URL, endpoint_for, fetch_hourly

TODAY = date(2026, 9, 30)


def test_endpoint_recent_day_uses_forecast():
    assert endpoint_for(date(2026, 9, 29), TODAY) == FORECAST_URL


def test_endpoint_old_day_uses_archive():
    assert endpoint_for(date(2025, 1, 1), TODAY) == ARCHIVE_URL


def test_endpoint_rejects_future_day():
    with pytest.raises(ValueError):
        endpoint_for(date(2026, 10, 1), TODAY)


@responses.activate
def test_fetch_hourly_sends_all_locations_in_one_call(locations):
    responses.get(
        FORECAST_URL,
        json=[api_item(), api_item()],
        match=[
            matchers.query_param_matcher(
                {
                    "latitude": "-10.0,-20.0",
                    "longitude": "-40.0,-50.0",
                    "start_date": "2026-09-29",
                    "end_date": "2026-09-29",
                    "timezone": "GMT",
                },
                strict_match=False,
            )
        ],
    )

    payload = fetch_hourly(date(2026, 9, 29), locations, session=requests.Session(), today=TODAY)

    assert len(payload) == 2


@responses.activate
def test_fetch_hourly_wraps_single_location(locations):
    responses.get(FORECAST_URL, json=api_item())

    session = requests.Session()
    payload = fetch_hourly(date(2026, 9, 29), locations[:1], session=session, today=TODAY)

    assert len(payload) == 1


@responses.activate
def test_fetch_hourly_rejects_wrong_location_count(locations):
    responses.get(FORECAST_URL, json=[api_item()])

    with pytest.raises(ValueError):
        fetch_hourly(date(2026, 9, 29), locations, session=requests.Session(), today=TODAY)


@responses.activate
def test_fetch_hourly_raises_on_http_error(locations):
    responses.get(FORECAST_URL, status=400, json={"error": True, "reason": "bad"})

    with pytest.raises(requests.HTTPError):
        fetch_hourly(date(2026, 9, 29), locations, session=requests.Session(), today=TODAY)
