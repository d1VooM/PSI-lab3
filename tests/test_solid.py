"""Тесты, которые доказывают выполнение SOLID (ссылка на них идёт в REPORT.md)."""
from datetime import date

import pytest

from app import create_app
from app.cache import JsonCache, MemoryCache
from app.errors import SourceError
from app.messages import Messages
from app.ports import AsteroidProvider, KeyValueStore, RatesProvider
from app.providers.bnm import BnmProvider
from app.providers.nasa import NasaNeoProvider
from app.services.neo import NeoService
from app.services.rates import RatesService

RATES = {"EUR": {"name": "Euro", "nominal": "1", "value": "20"}, "MDL": {"name": "Leu", "nominal": "1", "value": "1"}}


# --- L: любая реализация хранилища взаимозаменяема, контракт один ---
@pytest.fixture(params=["json", "memory"])
def store(request, tmp_path):
    return JsonCache(tmp_path / "c.json") if request.param == "json" else MemoryCache()


def test_store_contract(store):
    assert store.get("x") is None
    store.set("x", {"a": 1})
    store.set("x", {"a": 2})
    assert store.get("x") == {"a": 2}


# --- D: сервис работает без сети и без диска, всё подставлено снаружи ---
class FakeProvider:
    name = "Fake bank"

    def __init__(self, data=None, fail=False):
        self.data, self.fail, self.calls = data or {}, fail, []

    def fetch_rates(self, day):
        self.calls.append(day)
        if self.fail:
            raise SourceError("тестовый сбой")
        return self.data


def test_service_depends_on_abstractions_only():
    svc = RatesService(FakeProvider(RATES), MemoryCache(), today=lambda: date(2026, 10, 27))
    p = svc.get_rates()
    assert p["source"] == "Fake bank" and p["rate_date"] == "2026-10-27"


# --- O: новый источник добавляется БЕЗ правки RatesService ---
def test_new_provider_needs_no_service_change():
    mem = MemoryCache()
    RatesService(FakeProvider(RATES), mem, today=lambda: date(2026, 10, 27)).get_rates()
    broken = RatesService(FakeProvider(fail=True), mem, today=lambda: date(2026, 10, 28))
    p = broken.get_rates()
    assert p["from_cache"] and "тестовый сбой" in p["warning"]


# --- O + L: тексты меняются наследованием, сервис не трогаем ---
class EnglishMessages(Messages):
    def rates_from_cache(self, reason, rate_date):
        return f"Using cached rate from {rate_date}"


def test_messages_are_replaceable():
    mem = MemoryCache()
    RatesService(FakeProvider(RATES), mem, today=lambda: date(2026, 10, 27)).get_rates()
    svc = RatesService(FakeProvider(fail=True), mem, EnglishMessages(), today=lambda: date(2026, 10, 28))
    assert svc.get_rates()["warning"] == "Using cached rate from 2026-10-27"


# --- I: узкие раздельные порты; конкретные классы им соответствуют ---
def test_ports_are_small_and_satisfied():
    assert isinstance(BnmProvider(), RatesProvider) and not isinstance(BnmProvider(), AsteroidProvider)
    assert isinstance(NasaNeoProvider(), AsteroidProvider) and not isinstance(NasaNeoProvider(), RatesProvider)
    assert isinstance(JsonCache("x.json"), KeyValueStore) and isinstance(MemoryCache(), KeyValueStore)


# --- S: сервис NEO не знает про HTTP/NASA ---
def test_neo_service_with_fake_provider():
    class P:
        name = "Fake NEO"

        def fetch_asteroids(self, iso):
            return [{"name": "A", "hazardous": True}, {"name": "B", "hazardous": False}]

    p = NeoService(P(), MemoryCache()).get("2026-10-27")
    assert p["count"] == 2 and p["hazardous_count"] == 1 and p["source"] == "Fake NEO"


# --- D: composition root принимает готовые сервисы ---
def test_create_app_accepts_injected_services(tmp_path):
    rs = RatesService(FakeProvider(RATES), MemoryCache(), today=lambda: date(2026, 10, 27))
    app = create_app({"CACHE_PATH": str(tmp_path / "x.json")}, rates_service=rs)
    r = app.test_client().post("/api/convert", json={"amount": "40", "from": "EUR", "to": "MDL"})
    assert r.get_json()["result"] == "800.0000"
