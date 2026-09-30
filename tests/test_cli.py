from datetime import date

import pytest
from conftest import BUCKET, fake_source

from ingestion import cli
from ingestion.sources import SOURCES


@pytest.fixture
def fake_sources(monkeypatch):
    """Substitui o registro por duas fontes e captura as execuções."""
    sources = {name: fake_source(name) for name in ("alpha", "beta")}
    calls = []
    monkeypatch.setattr(cli, "SOURCES", sources)
    monkeypatch.setattr(cli, "run_source", lambda source, day, _: calls.append((source.name, day)))
    monkeypatch.setenv("BRONZE_BUCKET", BUCKET)
    return calls


def test_open_meteo_sources_are_registered():
    assert {"open_meteo", "open_meteo_locations"} <= set(SOURCES)


def test_missing_platform_env_has_actionable_error(monkeypatch):
    monkeypatch.delenv("BRONZE_BUCKET", raising=False)

    with pytest.raises(RuntimeError, match="platform/local.env"):
        cli.main(["run", "open_meteo"])


def test_run_without_sources_runs_all(fake_sources):
    assert cli.main(["run", "--date", "2026-09-29"]) == 0

    assert fake_sources == [("alpha", date(2026, 9, 29)), ("beta", date(2026, 9, 29))]


def test_run_selected_source_only(fake_sources):
    assert cli.main(["run", "beta", "beta", "--date", "2026-09-29"]) == 0

    assert fake_sources == [("beta", date(2026, 9, 29))]


def test_unknown_source_is_rejected(fake_sources):
    with pytest.raises(SystemExit) as exc:
        cli.main(["run", "gamma"])

    assert exc.value.code == 2
    assert fake_sources == []


def test_failure_does_not_stop_other_sources(monkeypatch, fake_sources):
    def run_source(source, day, _):
        if source.name == "alpha":
            raise RuntimeError("API fora do ar")
        fake_sources.append((source.name, day))

    monkeypatch.setattr(cli, "run_source", run_source)

    assert cli.main(["run", "--date", "2026-09-29"]) == 1
    assert fake_sources == [("beta", date(2026, 9, 29))]


def test_list_does_not_need_environment(monkeypatch, fake_sources, capsys):
    monkeypatch.delenv("BRONZE_BUCKET")

    assert cli.main(["list"]) == 0
    assert "alpha" in capsys.readouterr().out


def test_every_run_logs_the_image_commit(monkeypatch, fake_sources, caplog):
    monkeypatch.setenv("BIGDATA_VERSION", "abc1234")

    with caplog.at_level("INFO", logger="ingestion"):
        cli.main(["run", "alpha", "--date", "2026-09-29"])

    assert "bigdata-ingestion commit abc1234" in caplog.text
