"""Конфигурация приложения и проверка пользовательских параметров."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

LATEST_VERSION = "latest"
ALLOWED_SCHEMES = ("http", "https")

PACKAGE_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
TEST_PACKAGE_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(
    r"^\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$"
)


class ConfigError(ValueError):
    """Ошибка в значении пользовательского параметра."""


@dataclass(frozen=True)
class Config:
    """Проверенные параметры, заданные пользователем."""

    package: str
    repo: str
    test_mode: bool
    version: str
    ascii_tree: bool
    filter_substring: str

    def as_pairs(self):
        """Возвращает параметры в виде списка пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("test_mode", self.test_mode),
            ("version", self.version),
            ("ascii_tree", self.ascii_tree),
            ("filter", self.filter_substring),
        ]


def validate_package(name, test_mode):
    """Проверяет имя пакета.

    В тестовом режиме имя состоит только из больших латинских букв.
    """
    name = name.strip()
    if not name:
        raise ConfigError("имя пакета не должно быть пустым")
    if test_mode and not TEST_PACKAGE_RE.match(name):
        raise ConfigError(
            f"имя тестового пакета '{name}' должно состоять "
            "только из больших латинских букв"
        )
    if not PACKAGE_RE.match(name):
        raise ConfigError(f"недопустимое имя пакета '{name}'")
    return name


def validate_url(url):
    """Проверяет, что строка является корректным http(s)-адресом."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ConfigError(
            f"'{url}' не является корректным URL (нужен http или https)"
        )
    return url


def validate_file(path):
    """Проверяет, что путь указывает на существующий читаемый файл."""
    if not os.path.exists(path):
        raise ConfigError(f"файл тестового репозитория '{path}' не найден")
    if not os.path.isfile(path):
        raise ConfigError(f"'{path}' не является файлом")
    if not os.access(path, os.R_OK):
        raise ConfigError(f"нет прав на чтение файла '{path}'")
    return path


def validate_repo(repo, test_mode):
    """Проверяет URL репозитория или путь к файлу тестового репозитория."""
    repo = repo.strip()
    if not repo:
        raise ConfigError("адрес или путь репозитория не задан")
    if test_mode:
        return validate_file(repo)
    return validate_url(repo)


def validate_version(version):
    """Проверяет версию пакета (упрощённый формат PEP 440)."""
    version = version.strip()
    if version == LATEST_VERSION:
        return version
    if not VERSION_RE.match(version):
        raise ConfigError(
            f"недопустимая версия '{version}' (пример: 1.2.3)"
        )
    return version


def validate_filter(substring):
    """Проверяет подстроку для фильтрации пакетов."""
    if substring is None:
        return ""
    substring = substring.strip()
    if not substring:
        raise ConfigError("подстрока фильтрации не должна быть пустой")
    if any(char.isspace() for char in substring):
        raise ConfigError("подстрока фильтрации не должна содержать пробелы")
    return substring


def build_config(package, repo, test_mode, version, ascii_tree, substring):
    """Проверяет все параметры и собирает из них объект Config."""
    return Config(
        package=validate_package(package, test_mode),
        repo=validate_repo(repo, test_mode),
        test_mode=test_mode,
        version=validate_version(version),
        ascii_tree=ascii_tree,
        filter_substring=validate_filter(substring),
    )


def format_config(config):
    """Форматирует параметры в строки вида «ключ: значение»."""
    lines = []
    for key, value in config.as_pairs():
        shown = str(value).lower() if isinstance(value, bool) else value
        lines.append(f"{key}: {shown}")
    return "\n".join(lines)
