from .client import Client


class TestRealDatabase:
    def test_get_predicted_wind_yields_for_location(self, forecast_values, db_session) -> None:
        locID = "testID"
        client = Client()
        out = client.get_predicted_wind_yields_for_location(locID)
        assert out is not None

    def test_get_predicted_solar_yields_for_location(self, forecast_values) -> None:
        locID = "testID"
        client = Client()
        out = client.get_predicted_solar_yields_for_location(locID)
        assert out is not None

    def test_get_actual_wind_yields_for_location(self, generations) -> None:
        locID = "testID"
        client = Client()
        out = client.get_actual_wind_yields_for_location(locID)
        assert out is not None

    def test_get_actual_solar_yields_for_location(self, generations) -> None:
        locID = "testID"
        client = Client()
        out = client.get_actual_solar_yields_for_location(locID)
        assert out is not None

    def test_get_wind_regions(self) -> None:
        client = Client()
        out = client.get_wind_regions()
        assert out is not None

    def test_get_solar_regions(self) -> None:
        client = Client()
        out = client.get_solar_regions()
        assert out is not None
