"""Источники данных о зависимостях: реальный и тестовый репозитории."""

from depgraph.config import LATEST_VERSION
from depgraph.errors import FetchError
from depgraph.fetcher import fetch_package_info
from depgraph.requirements import collect_direct_dependencies
from depgraph.testrepo import load_test_repo


class PypiProvider:
    """Получает прямые зависимости пакетов из репозитория по URL.

    Для корневого пакета берётся заданная версия, для остальных —
    последняя доступная.
    """

    def __init__(self, repo, root, version):
        """Запоминает URL репозитория, корневой пакет и его версию."""
        self.repo = repo
        self.root = root
        self.version = version

    def __call__(self, name):
        """Возвращает имена прямых зависимостей пакета."""
        version = self.version if name == self.root else LATEST_VERSION
        info = fetch_package_info(self.repo, name, version)
        return [dep.name for dep in collect_direct_dependencies(info.requires)]


class FileRepoProvider:
    """Получает прямые зависимости из таблицы тестового репозитория."""

    def __init__(self, table, root):
        """Проверяет, что корневой пакет описан в таблице."""
        if root not in table:
            raise FetchError(f"пакет '{root}' не описан в тестовом файле")
        self.table = table

    def __call__(self, name):
        """Возвращает зависимости пакета; неописанный пакет — без них."""
        return self.table.get(name, [])


def make_provider(config):
    """Создаёт источник данных в соответствии с настройками."""
    if config.test_mode:
        return FileRepoProvider(load_test_repo(config.repo), config.package)
    return PypiProvider(config.repo, config.package, config.version)
