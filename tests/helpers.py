import requests

BNM_XML = """<ValCurs Date="23.10.2026" name="Official exchange rates">
<Valute ID="44"><NumCode>840</NumCode><CharCode>USD</CharCode><Nominal>1</Nominal><Name>US Dollar</Name><Value>17.5000</Value></Valute>
<Valute ID="47"><NumCode>978</NumCode><CharCode>EUR</CharCode><Nominal>1</Nominal><Name>Euro</Name><Value>20.0000</Value></Valute>
<Valute ID="12"><NumCode>392</NumCode><CharCode>JPY</CharCode><Nominal>100</Nominal><Name>Japanese Yen</Name><Value>12.0000</Value></Valute>
</ValCurs>"""
EMPTY_XML = '<ValCurs Date="25.10.2026" name="Official exchange rates"></ValCurs>'

NEO_JSON = {"near_earth_objects": {"2026-10-27": [
    {"id": "1", "name": "(2020 AB)", "is_potentially_hazardous_asteroid": False,
     "estimated_diameter": {"meters": {"estimated_diameter_min": 10.0, "estimated_diameter_max": 22.5}},
     "close_approach_data": [{"close_approach_date_full": "2026-Oct-27 10:00",
                              "relative_velocity": {"kilometers_per_second": "12.3"},
                              "miss_distance": {"kilometers": "7500000", "lunar": "19.5"}}]},
    {"id": "2", "name": "(2019 XY)", "is_potentially_hazardous_asteroid": True,
     "estimated_diameter": {"meters": {"estimated_diameter_min": 150.0, "estimated_diameter_max": 340.0}},
     "close_approach_data": [{"relative_velocity": {"kilometers_per_second": "20.1"},
                              "miss_distance": {"kilometers": "1200000", "lunar": "3.1"}}]},
]}}


class Resp:
    def __init__(self, text="", status=200, json_data=None):
        self.text, self.status_code, self._json = text, status, json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def offline(*args, **kwargs):
    raise requests.ConnectionError("network down")
