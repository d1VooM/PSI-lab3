from datetime import date

import pytest

from app import create_app
from app.providers.bnm import BnmProvider
from app.providers.nasa import NasaNeoProvider
from app.services.neo import NeoService
from app.services.rates import RatesService
from tests.helpers import BNM_XML, NEO_JSON, Resp, offline


@pytest.fixture
def client(tmp_path):
    app = create_app({"CACHE_PATH": str(tmp_path / "c.json"), "TESTING": True})
    store = app.extensions["rates"].store
    app.extensions["rates"] = RatesService(BnmProvider(lambda *a, **k: Resp(BNM_XML)), store,
                                           today=lambda: date(2026, 10, 27))
    app.extensions["neo"] = NeoService(NasaNeoProvider(http_get=lambda *a, **k: Resp(json_data=NEO_JSON)), store)
    return app.test_client()


def post(client, **body):
    return client.post("/api/convert", json=body)


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200 and "Конвертер валют".encode() in r.data


def test_rates_endpoint(client):
    d = client.get("/api/rates").get_json()
    assert [c["code"] for c in d["currencies"]][:3] == ["MDL", "EUR", "USD"]
    assert d["source"] and d["rate_date"]


def test_convert_and_reverse(client):
    a = post(client, amount="100", **{"from": "USD", "to": "EUR"}).get_json()
    b = post(client, amount="87.5", **{"from": "EUR", "to": "USD"}).get_json()
    assert a["result"] == "87.5000" and b["result"] == "100.0000"
    assert a["source"] and a["rate_date"]


def test_convert_same_currency(client):
    d = post(client, amount="5", **{"from": "EUR", "to": "EUR"}).get_json()
    assert d["same_currency"] and d["result"] == "5.0000"


@pytest.mark.parametrize("amount", ["", "abc", "-1", "0", None])
def test_convert_invalid_amount_is_400(client, amount):
    r = post(client, amount=amount, **{"from": "EUR", "to": "USD"})
    assert r.status_code == 400 and r.get_json()["error"]


def test_convert_unknown_currency_400(client):
    assert post(client, amount="1", **{"from": "EUR", "to": "ZZZ"}).status_code == 400


def test_neo_endpoint_and_errors(client):
    ok = client.get("/api/neo?date=2026-10-27").get_json()
    assert ok["count"] == 2 and ok["source"] == "NASA NeoWs API" and ok["fetched_at"]
    assert client.get("/api/neo?date=2026-02-31").status_code == 400
    assert client.get("/api/neo").status_code == 400


def test_app_survives_network_loss_with_cache(client):
    client.get("/api/rates")  # прогреваем кэш
    client.application.extensions["rates"].provider.http_get = offline
    d = client.get("/api/rates").get_json()
    assert d["from_cache"] and d["warning"]
    assert post(client, amount="10", **{"from": "EUR", "to": "MDL"}).status_code == 200


def test_no_network_no_cache_is_503_not_crash(tmp_path):
    app = create_app({"CACHE_PATH": str(tmp_path / "none.json"), "TESTING": True})
    app.extensions["rates"].provider.http_get = offline
    r = app.test_client().get("/api/rates")
    assert r.status_code == 503 and r.get_json()["error"]
