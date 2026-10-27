from decimal import Decimal

import pytest

from app.errors import ValidationError
from app.validation import parse_amount, parse_date


@pytest.mark.parametrize("raw,expected", [("100", "100"), ("12,5", "12.5"), (" 1 000.25 ", "1000.25"), (5, "5")])
def test_amount_ok(raw, expected):
    assert parse_amount(raw) == Decimal(expected)


@pytest.mark.parametrize("raw,part", [
    ("", "Введите"), (None, "Введите"), ("   ", "Введите"), ("abc", "числом"), ("12abc", "числом"),
    ("1e5", "числом"), ("NaN", "числом"), ("-5", "отрицательной"), ("0", "больше нуля"),
    ("0.00", "больше нуля"), ("1" + "0" * 13, "большая"),
])
def test_amount_invalid(raw, part):
    with pytest.raises(ValidationError, match=part):
        parse_amount(raw)


def test_date_ok():
    assert parse_date("2026-10-27").isoformat() == "2026-10-27"
    assert parse_date("2024-02-29").day == 29  # високосный год


@pytest.mark.parametrize("raw", ["", None, "27.10.2026", "2026/10/27", "2026-1-5", "abcd-ef-gh", "2026-02-31",
                                 "2025-02-29", "2026-13-01", "2026-00-10", "1800-01-01"])
def test_date_invalid(raw):
    with pytest.raises(ValidationError):
        parse_date(raw)
