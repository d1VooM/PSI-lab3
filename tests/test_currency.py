from datetime import date
from decimal import Decimal

import pytest

from app.cache import JsonCache
from app.converter import convert, quantize
from app.errors import SourceError, SourceUnavailable, ValidationError
from app.providers.bnm import BnmProvider, parse_bnm_xml
from app.services.rates import RatesService as _Rates
from tests.helpers import BNM_XML, EMPTY_XML, Resp, offline

SUNDAY = date(2026, 10, 25)


def RatesService(cache, http_get, today):
    return _Rates(BnmProvider(http_get), cache, today=today)


def rates():
    return parse_bnm_xml(BNM_XML) | {"MDL": {"name": "Leu", "nominal": "1", "value": "1"}}


# --- разбор ответа ---
def test_parse_ok():
    r = parse_bnm_xml(BNM_XML)
    assert set(r) == {"USD", "EUR", "JPY"}
    assert r["JPY"]["nominal"] == "100" and r["EUR"]["value"] == "20.0000"


def test_parse_empty_and_blank():
    assert parse_bnm_xml("") == {}
    assert parse_bnm_xml("   ") == {}
    assert parse_bnm_xml(EMPTY_XML) == {}


def test_parse_garbage_raises():
    with pytest.raises(SourceError):
        parse_bnm_xml("<html><body>502 Bad gateway")


def test_parse_skips_broken_rows():
    xml = "<V><Valute><CharCode>XXX</CharCode><Nominal>1</Nominal><Value>abc</Value></Valute>" \
          "<Valute><CharCode>YYY</CharCode><Nominal>0</Nominal><Value>5</Value></Valute></V>"
    assert parse_bnm_xml(xml) == {}


# --- расчёт ---
def test_convert_both_directions():
    r = rates()
    res, rate = convert(Decimal(10), "EUR", "USD", r)
    assert quantize(res, 4) == Decimal("11.4286")
    back, _ = convert(Decimal(100), "USD", "EUR", r)
    assert back == Decimal("87.5")


def test_convert_nominal_and_mdl():
    r = rates()
    assert convert(Decimal(100), "JPY", "MDL", r)[0] == Decimal(12)
    assert convert(Decimal(20), "MDL", "EUR", r)[0] == Decimal(1)


def test_convert_same_currency_no_error():
    res, rate = convert(Decimal("42.5"), "EUR", "EUR", rates())
    assert res == Decimal("42.5") and rate == 1


def test_convert_unknown_currency():
    with pytest.raises(ValidationError):
        convert(Decimal(1), "EUR", "XXX", rates())


# --- сервис: выходные, сеть, кэш ---
def test_weekend_falls_back_to_last_published(tmp_path):
    seen = []

    def get(url, params, timeout):
        seen.append(params["date"])
        return Resp(BNM_XML if params["date"] == "23.10.2026" else EMPTY_XML)

    svc = RatesService(JsonCache(tmp_path / "c.json"), http_get=get, today=lambda: SUNDAY)
    p = svc.get_rates()
    assert seen == ["25.10.2026", "24.10.2026", "23.10.2026"]
    assert p["rate_date"] == "2026-10-23" and "23.10.2026" in p["warning"] and not p["from_cache"]


def test_fresh_rate_has_no_warning(tmp_path):
    svc = RatesService(JsonCache(tmp_path / "c.json"), http_get=lambda *a, **k: Resp(BNM_XML), today=lambda: SUNDAY)
    assert svc.get_rates()["warning"] is None


def test_offline_uses_cache_that_survives_restart(tmp_path):
    path = tmp_path / "c.json"
    RatesService(JsonCache(path), http_get=lambda *a, **k: Resp(BNM_XML), today=lambda: SUNDAY).get_rates()
    # «перезапуск»: новые объекты, сети нет
    p = RatesService(JsonCache(path), http_get=offline, today=lambda: SUNDAY).get_rates()
    assert p["from_cache"] is True and "от 25.10.2026" in p["warning"] and "EUR" in p["rates"]


def test_offline_without_cache_raises(tmp_path):
    svc = RatesService(JsonCache(tmp_path / "c.json"), http_get=offline, today=lambda: SUNDAY)
    with pytest.raises(SourceUnavailable):
        svc.get_rates()


def test_http_error_and_bad_xml_fall_back(tmp_path):
    cache = JsonCache(tmp_path / "c.json")
    RatesService(cache, http_get=lambda *a, **k: Resp(BNM_XML), today=lambda: SUNDAY).get_rates()
    for bad in (Resp(status=503), Resp("<oops")):
        p = RatesService(cache, http_get=lambda *a, _b=bad, **k: _b, today=lambda: SUNDAY).get_rates()
        assert p["from_cache"]


def test_source_empty_for_a_week_uses_cache(tmp_path):
    cache = JsonCache(tmp_path / "c.json")
    RatesService(cache, http_get=lambda *a, **k: Resp(BNM_XML), today=lambda: SUNDAY).get_rates()
    p = RatesService(cache, http_get=lambda *a, **k: Resp(EMPTY_XML), today=lambda: SUNDAY).get_rates()
    assert p["from_cache"]
