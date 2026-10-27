import re
from datetime import datetime
from decimal import Decimal

from .errors import ValidationError

MAX_AMOUNT = Decimal("1000000000000")
_NUMBER = re.compile(r"^[+-]?\d+(\.\d+)?$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_amount(raw):
    s = "" if raw is None else str(raw).strip().replace(" ", "").replace(",", ".")
    if not s:
        raise ValidationError("Введите сумму")
    if not _NUMBER.match(s):
        raise ValidationError("Сумма должна быть числом")
    value = Decimal(s)
    if value < 0:
        raise ValidationError("Сумма не может быть отрицательной")
    if value == 0:
        raise ValidationError("Сумма должна быть больше нуля")
    if value > MAX_AMOUNT:
        raise ValidationError("Сумма слишком большая")
    return value


def parse_date(raw):
    s = "" if raw is None else str(raw).strip()
    if not s:
        raise ValidationError("Введите дату в формате ГГГГ-ММ-ДД")
    if not _DATE.match(s):
        raise ValidationError("Неверный формат даты. Нужно ГГГГ-ММ-ДД, например 2026-10-27")
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Такой даты не существует в календаре")
    if not 1900 <= d.year <= 2100:
        raise ValidationError("Год должен быть между 1900 и 2100")
    return d
