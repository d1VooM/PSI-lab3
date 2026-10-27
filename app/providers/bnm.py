import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

import requests

from ..errors import SourceError

BNM_URL = "https://www.bnm.md/en/official_exchange_rates"
MDL = {"name": "Moldovan Leu", "nominal": "1", "value": "1"}


def parse_bnm_xml(text):
    """XML НБМ -> {код: {name, nominal, value}}. Пустой ответ даёт {}."""
    if text is None or not text.strip():
        return {}
    try:
        root = ET.fromstring(text.strip())
    except ET.ParseError as exc:
        raise SourceError("источник вернул некорректный XML") from exc
    rates = {}
    for v in root.iter("Valute"):
        code = (v.findtext("CharCode") or "").strip().upper()
        try:
            nominal = Decimal((v.findtext("Nominal") or "").strip())
            value = Decimal((v.findtext("Value") or "").strip().replace(",", "."))
        except InvalidOperation:
            continue
        if not code or nominal <= 0 or value <= 0:
            continue
        rates[code] = {"name": (v.findtext("Name") or code).strip(),
                       "nominal": str(nominal), "value": str(value)}
    return rates


class BnmProvider:
    """Реализация RatesProvider для НБМ. Только сеть + разбор XML (S)."""
    name = "Национальный банк Молдовы (bnm.md)"

    def __init__(self, http_get=requests.get, timeout=10):
        self.http_get, self.timeout = http_get, timeout

    def fetch_rates(self, day):
        try:
            resp = self.http_get(BNM_URL, params={"get_xml": 1, "date": day.strftime("%d.%m.%Y")},
                                 timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise SourceError("нет связи с сайтом НБМ") from exc
        rates = parse_bnm_xml(resp.text)
        if rates:
            rates["MDL"] = dict(MDL)  # базовая валюта НБМ
        return rates
