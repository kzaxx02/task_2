"""Исключения приложения."""


class DepgraphError(Exception):
    """Базовая ошибка приложения, понятная пользователю."""


class ConfigError(DepgraphError):
    """Ошибка в значении пользовательского параметра."""


class FetchError(DepgraphError):
    """Ошибка получения или разбора данных из репозитория."""


class RequirementError(DepgraphError):
    """Ошибка разбора строки зависимости."""
