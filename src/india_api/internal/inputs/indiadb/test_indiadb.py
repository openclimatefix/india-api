import pytest

from .client import Client


@pytest.fixture(scope="session")
def client(engine):
    return Client(database_url=engine.url)


class TestIndiaDBClient:

    def test_get_predicted_wind_yields_for_location(self, client) -> None:
        locID = "testID"
        out = client.get_predicted_wind_yields_for_location(locID)
        assert out is not None

    def test_get_predicted_solar_yields_for_location(self, client) -> None:
        locID = "testID"
        out = client.get_predicted_solar_yields_for_location(locID)
        assert out is not None

    def test_get_actual_wind_yields_for_location(self, client) -> None:
        locID = "testID"
        out = client.get_actual_wind_yields_for_location(locID)
        assert out is not None

    def test_get_actual_solar_yields_for_location(self, client) -> None:
        locID = "testID"
        out = client.get_actual_solar_yields_for_location(locID)
        assert out is not None

    def test_get_wind_regions(self, client) -> None:
        out = client.get_wind_regions()
        assert len(out) == 1
        assert out[0] == "ruvnl"

    def test_get_solar_regions(self, client) -> None:
        out = client.get_solar_regions()
        assert len(out) == 1
        assert out[0] == "ruvnl"
