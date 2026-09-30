import pytest
import requests
import responses

from ingestion.sources.rest_countries.client import API_URL, api_key, fetch_countries


def page(objects, more):
    return {"data": {"objects": objects, "meta": {"count": len(objects), "more": more}}}


@responses.activate
def test_pages_follow_offset_until_more_is_false():
    responses.get(API_URL, json=page([{"codes": {"alpha_3": "BRA"}}] * 100, more=True))
    responses.get(API_URL, json=page([{"codes": {"alpha_3": "URY"}}], more=False))

    countries = fetch_countries(session=requests.Session(), key="k")

    assert len(countries) == 101
    assert [call.request.params["offset"] for call in responses.calls] == ["0", "100"]
    assert responses.calls[0].request.headers["Authorization"] == "Bearer k"


@responses.activate
def test_error_envelope_with_http_200_fails():
    # Formato da resposta da API descontinuada (v3.1), que chega com HTTP 200.
    responses.get(
        API_URL,
        json={"success": False, "data": None, "errors": [{"message": "deprecated"}]},
    )

    with pytest.raises(RuntimeError, match="deprecated"):
        fetch_countries(session=requests.Session(), key="k")


@responses.activate
def test_invalid_key_fails_with_status():
    responses.get(API_URL, status=401, json={"data": None, "errors": [{"message": "invalid key"}]})

    with pytest.raises(RuntimeError, match="HTTP 401"):
        fetch_countries(session=requests.Session(), key="k")


def test_missing_key_explains_where_to_set_it(monkeypatch):
    monkeypatch.delenv("REST_COUNTRIES_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="platform/secrets.env"):
        api_key()
