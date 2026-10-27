"""Абстракции (порты). Сервисы зависят только от них (D),
а не от конкретных HTTP-клиентов и файлов. Интерфейсы узкие и раздельные (I)."""
from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class KeyValueStore(Protocol):
    def get(self, key: str): ...
    def set(self, key: str, value) -> None: ...


@runtime_checkable
class RatesProvider(Protocol):
    name: str

    def fetch_rates(self, day: date) -> dict:
        """{код: {name, nominal, value}} за день. Пустой dict, если курс не опубликован.
        При сбое бросает SourceError."""


@runtime_checkable
class AsteroidProvider(Protocol):
    name: str

    def fetch_asteroids(self, iso_date: str) -> list:
        """Список астероидов за день ([] если данных нет). При сбое бросает SourceError."""
