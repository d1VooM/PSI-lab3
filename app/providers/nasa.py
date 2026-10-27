import requests

from ..errors import SourceError

NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_neo(data, iso_date):
    if not isinstance(data, dict) or not isinstance(data.get("near_earth_objects"), dict):
        raise SourceError("ответ NASA имеет неожиданный формат")
    out = []
    for a in data["near_earth_objects"].get(iso_date) or []:
        cad = (a.get("close_approach_data") or [{}])[0]
        dia = (a.get("estimated_diameter") or {}).get("meters") or {}
        miss = cad.get("miss_distance") or {}
        out.append({
            "id": a.get("id"),
            "name": (a.get("name") or "").strip("() ") or "Без имени",
            "hazardous": bool(a.get("is_potentially_hazardous_asteroid")),
            "diameter_min_m": _num(dia.get("estimated_diameter_min")),
            "diameter_max_m": _num(dia.get("estimated_diameter_max")),
            "velocity_kms": _num((cad.get("relative_velocity") or {}).get("kilometers_per_second")),
            "miss_km": _num(miss.get("kilometers")),
            "miss_lunar": _num(miss.get("lunar")),
            "approach_time": cad.get("close_approach_date_full"),
            "url": a.get("nasa_jpl_url"),
        })
    out.sort(key=lambda x: x["miss_km"] if x["miss_km"] is not None else float("inf"))
    return out


class NasaNeoProvider:
    """Реализация AsteroidProvider для NASA NeoWs."""
    name = "NASA NeoWs API"

    def __init__(self, api_key="DEMO_KEY", http_get=requests.get, timeout=15):
        self.api_key, self.http_get, self.timeout = api_key, http_get, timeout

    def fetch_asteroids(self, iso_date):
        try:
            resp = self.http_get(NEO_URL, params={"start_date": iso_date, "end_date": iso_date,
                                                  "api_key": self.api_key}, timeout=self.timeout)
            resp.raise_for_status()
            return parse_neo(resp.json(), iso_date)
        except (requests.RequestException, ValueError) as exc:
            raise SourceError("сервис NASA недоступен или вернул ошибку") from exc
