"""Чистая доменная логика расчёта: без сети, диска и Flask (S)."""
from decimal import ROUND_HALF_UP, Decimal

from .errors import ValidationError


def _mdl_per_unit(rate):
    return Decimal(rate["value"]) / Decimal(rate["nominal"])


def convert(amount, src, dst, rates):
    """Возвращает (результат, курс 1 src = rate dst)."""
    for code in (src, dst):
        if code not in rates:
            raise ValidationError(f"Валюта {code} недоступна")
    if src == dst:
        return amount, Decimal(1)
    rate = _mdl_per_unit(rates[src]) / _mdl_per_unit(rates[dst])
    return amount * rate, rate


def quantize(value, places):
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
