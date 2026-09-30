import pytest

from ingestion.config import HOURLY_VARIABLES, Location

LOCATIONS = (
    Location("Cidade A", -10.0, -40.0),
    Location("Cidade B", -20.0, -50.0),
)


def api_item(hours: int = 24, day: str = "2026-09-29") -> dict:
    hourly = {"time": [f"{day}T{h:02d}:00" for h in range(hours)]}
    for variable in HOURLY_VARIABLES:
        hourly[variable] = [float(h) for h in range(hours)]
    hourly["weather_code"] = [3] * hours
    return {"latitude": 0.0, "longitude": 0.0, "hourly": hourly}


@pytest.fixture
def locations():
    return LOCATIONS


@pytest.fixture
def payload():
    return [api_item(), api_item()]
