"""Тексты для пользователя. Отдельный класс (S): сервисы не знают формулировок,
а язык/тон меняется наследованием без правки сервисов (O)."""


def ru_date(iso):
    return ".".join(reversed(iso.split("-")))


def _cap(s):
    return s[:1].upper() + s[1:]


class Messages:
    def weekend_fallback(self, requested, used):
        return (f"На {ru_date(requested)} курс не опубликован (выходной или праздник). "
                f"Использован последний доступный курс от {ru_date(used)}.")

    def rates_from_cache(self, reason, rate_date):
        return (f"Не удалось обновить курс: {reason}. "
                f"Работаем с последним сохранённым курсом от {ru_date(rate_date)}.")

    def rates_unavailable(self, reason):
        return (f"Не удалось получить курсы: {reason}. "
                "Сохранённых данных пока нет, подключитесь к сети и повторите.")

    def rates_lookback(self, days):
        return f"НБМ не публиковал курсы последние {days} дней"

    def neo_no_data(self, iso):
        return f"на {ru_date(iso)} NASA не вернул данных"

    def neo_from_cache(self, reason, cached_date):
        return f"{_cap(reason)}. Показан последний сохранённый день: {ru_date(cached_date)}."

    def neo_unavailable(self, reason):
        return f"{_cap(reason)}, сохранённых данных нет."

    def neo_empty(self, reason):
        return f"{_cap(reason)}, а сохранённых данных ещё нет."
