import pytest

from app.cache import JsonCache
from app.errors import SourceError, SourceUnavailable, ValidationError
from app.providers.nasa import NasaNeoProvider, parse_neo
from app.services.neo import NeoService as _Neo
from tests.helpers import NEO_JSON, Resp, offline


def test_parse_neo_fields_and_sorting():
    a = parse_neo(NEO_JSON, "2026-10-27")
    assert [x["name"] for x in a] == ["2019 XY", "2020 AB"]  # ближайший первым
    assert a[0]["hazardous"] is True and a[1]["hazardous"] is False
    assert a[1]["diameter_max_m"] == 22.5 and a[1]["velocity_kms"] == 12.3 and a[1]["miss_km"] == 7500000.0


def test_parse_neo_empty_day_and_bad_format():
    assert parse_neo({"near_earth_objects": {}}, "2026-10-27") == []
    with pytest.raises(SourceError):
        parse_neo({"error": "x"}, "2026-10-27")
    with pytest.raises(SourceError):
        parse_neo([], "2026-10-27")


def test_parse_neo_tolerates_missing_fields():
    a = parse_neo({"near_earth_objects": {"2026-10-27": [{"id": "9"}]}}, "2026-10-27")[0]
    assert a["name"] == "Без имени" and a["miss_km"] is None and a["hazardous"] is False


def NeoService(cache, http_get):
    return _Neo(NasaNeoProvider(http_get=http_get), cache)


def make(tmp_path, get):
    return NeoService(JsonCache(tmp_path / "c.json"), http_get=get)


def test_get_success_caches(tmp_path):
    svc = make(tmp_path, lambda *a, **k: Resp(json_data=NEO_JSON))
    p = svc.get("2026-10-27")
    assert p["count"] == 2 and p["hazardous_count"] == 1 and p["warning"] is None
    assert svc.store.get("neo")["date"] == "2026-10-27"


def test_invalid_date_never_hits_network(tmp_path):
    def boom(*a, **k):
        raise AssertionError("network must not be called")
    svc = make(tmp_path, boom)
    for bad in ("2026-02-31", "27-10-2026", ""):
        with pytest.raises(ValidationError):
            svc.get(bad)


def test_empty_day_returns_last_cached_with_warning(tmp_path):
    cache = JsonCache(tmp_path / "c.json")
    NeoService(cache, http_get=lambda *a, **k: Resp(json_data=NEO_JSON)).get("2026-10-27")
    empty = Resp(json_data={"near_earth_objects": {}})
    p = NeoService(cache, http_get=lambda *a, **k: empty).get("2026-11-01")
    assert p["from_cache"] and p["date"] == "2026-10-27" and p["requested_date"] == "2026-11-01"
    assert "27.10.2026" in p["warning"] and p["count"] == 2


def test_empty_day_without_cache_is_not_an_error(tmp_path):
    p = make(tmp_path, lambda *a, **k: Resp(json_data={"near_earth_objects": {}})).get("2026-11-01")
    assert p["asteroids"] == [] and p["warning"]


def test_offline_and_rate_limit(tmp_path):
    with pytest.raises(SourceUnavailable):
        make(tmp_path, offline).get("2026-10-27")
    cache = JsonCache(tmp_path / "c2.json")
    NeoService(cache, http_get=lambda *a, **k: Resp(json_data=NEO_JSON)).get("2026-10-27")
    limited = NeoService(cache, http_get=lambda *a, **k: Resp(status=429)).get("2026-10-28")
    assert limited["from_cache"] and limited["count"] == 2
