from datetime import date, datetime, timedelta, timezone

from ..errors import SourceError, SourceUnavailable
from ..messages import Messages
from ..ports import KeyValueStore, RatesProvider


class RatesService:
    """Сценарий «получить курс»: провайдер -> откат по датам -> кэш.
    Зависит только от портов RatesProvider и KeyValueStore (D)."""

    def __init__(self, provider: RatesProvider, store: KeyValueStore,
                 messages: Messages = None, today=date.today, lookback=7):
        self.provider, self.store = provider, store
        self.messages = messages or Messages()
        self.today, self.lookback = today, lookback

    def get_rates(self):
        requested = self.today()
        try:
            for i in range(self.lookback + 1):
                day = requested - timedelta(days=i)
                rates = self.provider.fetch_rates(day)
                if not rates:
                    continue
                payload = {
                    "source": self.provider.name,
                    "requested_date": requested.isoformat(),
                    "rate_date": day.isoformat(),
                    "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "rates": rates, "from_cache": False, "warning": None,
                }
                self.store.set("rates", payload)
                if i:
                    return {**payload, "warning": self.messages.weekend_fallback(
                        payload["requested_date"], payload["rate_date"])}
                return payload
            reason = self.messages.rates_lookback(self.lookback)
        except SourceError as exc:
            reason = str(exc)
        return self._from_cache(reason)

    def _from_cache(self, reason):
        cached = self.store.get("rates")
        if not cached:
            raise SourceUnavailable(self.messages.rates_unavailable(reason))
        return {**cached, "from_cache": True,
                "warning": self.messages.rates_from_cache(reason, cached["rate_date"])}
