import unittest

from .client import Client

client = Client()

class TestDummyDatabase(unittest.TestCase):
    def test_get_predicted_wind_yields_for_location(self) -> None:
        locID = "testID"
        out = client.get_predicted_wind_yields_for_location(locID)
        self.assertIsNotNone(out)

    def test_get_predicted_solar_yields_for_location(self) -> None:
        locID = "testID"
        out = client.get_predicted_solar_yields_for_location(locID)
        self.assertIsNotNone(out)

    def test_get_actual_wind_yields_for_location(self) -> None:
        locID = "testID"
        out = client.get_actual_wind_yields_for_location(locID)
        self.assertIsNotNone(out)

    def test_get_actual_solar_yields_for_location(self) -> None:
        locID = "testID"
        out = client.get_actual_solar_yields_for_location(locID)
        self.assertIsNotNone(out)
