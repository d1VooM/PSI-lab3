class ValidationError(ValueError):
    """Некорректный ввод пользователя."""


class SourceError(Exception):
    """Источник данных недоступен или вернул мусор."""


class SourceUnavailable(Exception):
    """Источник недоступен и сохранённых данных тоже нет."""
