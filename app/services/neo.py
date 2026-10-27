from datetime import datetime, timezone

from ..errors import SourceError, SourceUnavailable
from ..messages import Messages
from ..ports import AsteroidProvider, KeyValueStore
from ..validation import parse_date


class NeoService:
    """Сценарий «астероиды на дату». Зависит от портов, не от NASA и не от файлов (D)."""

    def __init__(self, provider: AsteroidProvider, store: KeyValueStore, messages: Messages = None):
        self.provider, self.store = provider, store
        self.messages = messages or Messages()

    def _now(self):
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def get(self, raw_date):
        iso = parse_date(raw_date).isoformat()
        try:
            asteroids = self.provider.fetch_asteroids(iso)
        except SourceError as exc:
            return self._fallback(iso, str(exc), failed=True)
        if not asteroids:
            return self._fallback(iso, self.messages.neo_no_data(iso), failed=False)
        payload = {
            "source": self.provider.name, "requested_date": iso, "date": iso,
            "fetched_at": self._now(), "asteroids": asteroids, "count": len(asteroids),
            "hazardous_count": sum(a["hazardous"] for a in asteroids),
            "from_cache": False, "warning": None,
        }
        self.store.set("neo", payload)
        return payload

    def _fallback(self, iso, reason, failed):
        cached = self.store.get("neo")
        if cached:
            return {**cached, "requested_date": iso, "from_cache": True,
                    "warning": self.messages.neo_from_cache(reason, cached["date"])}
        if failed:
            raise SourceUnavailable(self.messages.neo_unavailable(reason))
        return {"source": self.provider.name, "requested_date": iso, "date": iso,
                "fetched_at": self._now(), "asteroids": [], "count": 0, "hazardous_count": 0,
                "from_cache": False, "warning": self.messages.neo_empty(reason)}
