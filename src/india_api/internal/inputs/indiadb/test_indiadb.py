import logging
import pytest

from india_api.internal import PredictedPower, ActualPower

from .client import Client

log = logging.getLogger(__name__)


@pytest.fixture()
def client(engine, db_session):
    """Hooks Client into pytest db_session fixture"""
    client = Client(database_url=str(engine.url))
    client.session = db_session

    return client


class TestIndiaDBClient:
    def test_get_predicted_wind_power_production_for_location(self, client, forecast_values) -> None:
        locID = "testID"
        result = client.get_predicted_wind_power_production_for_location(locID)

        assert len(result) == 110
        for record in result:
            assert isinstance(record, PredictedPower)

    def test_get_predicted_solar_power_production_for_location(self, client, forecast_values) -> None:
        locID = "testID"
        result = client.get_predicted_solar_power_production_for_location(locID)

        assert len(result) == 110
        for record in result:
            assert isinstance(record, PredictedPower)

    def test_get_actual_wind_power_production_for_location(self, client, generations) -> None:
        locID = "testID"
        result = client.get_actual_wind_power_production_for_location(locID)

        assert len(result) == 10
        for record in result:
            assert isinstance(record, ActualPower)

    def test_get_actual_solar_power_production_for_location(self, client, generations) -> None:
        locID = "testID"
        result = client.get_actual_solar_power_production_for_location(locID)

        assert len(result) == 10
        for record in result:
            assert isinstance(record, ActualPower)

    def test_get_wind_regions(self, client) -> None:
        result = client.get_wind_regions()
        assert len(result) == 1
        assert result[0] == "ruvnl"

    def test_get_solar_regions(self, client) -> None:
        result = client.get_solar_regions()
        assert len(result) == 1
        assert result[0] == "ruvnl"
