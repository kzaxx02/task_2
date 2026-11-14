"""Получение метаданных пакета из репозитория по HTTP."""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import quote

from depgraph.config import LATEST_VERSION
from depgraph.errors import FetchError

REQUEST_TIMEOUT = 15
USER_AGENT = "depgraph/0.2"


@dataclass(frozen=True)
class PackageInfo:
    """Метаданные пакета: имя, найденная версия и строки зависимостей."""

    package: str
    version: str
    requires: list


def build_metadata_url(repo, package, version):
    """Формирует URL JSON-описания пакета (формат PyPI JSON API)."""
    base = repo.rstrip("/")
    name = quote(package, safe="")
    if version == LATEST_VERSION:
        return f"{base}/pypi/{name}/json"
    return f"{base}/pypi/{name}/{quote(version, safe='')}/json"


def describe_http_error(error, url):
    """Возвращает понятное описание HTTP-ошибки."""
    if error.code == HTTPStatus.NOT_FOUND:
        return f"пакет или версия не найдены в репозитории ({url})"
    return f"репозиторий вернул ошибку HTTP {error.code} ({url})"


def parse_json(payload, url):
    """Разбирает тело ответа как JSON-объект."""
    try:
        data = json.loads(payload.decode("utf-8"))
    except ValueError as error:
        raise FetchError(f"ответ {url} не является корректным JSON") from error
    if not isinstance(data, dict):
        raise FetchError(f"ответ {url} имеет неожиданный формат")
    return data


def fetch_json(url, timeout=REQUEST_TIMEOUT):
    """Загружает JSON по URL, преобразуя сбои в FetchError."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        raise FetchError(describe_http_error(error, url)) from error
    except OSError as error:
        raise FetchError(f"не удалось подключиться к {url}: {error}") from error
    return parse_json(payload, url)


def extract_info(data, package, version):
    """Извлекает PackageInfo из разобранного ответа репозитория."""
    info = data.get("info")
    if not isinstance(info, dict):
        raise FetchError("в ответе репозитория нет раздела 'info'")
    requires = info.get("requires_dist") or []
    valid = isinstance(requires, list) and all(
        isinstance(item, str) for item in requires
    )
    if not valid:
        raise FetchError("поле 'requires_dist' имеет неверный формат")
    return PackageInfo(package, str(info.get("version") or version), requires)


def fetch_package_info(repo, package, version):
    """Получает метаданные заданной версии пакета из репозитория."""
    url = build_metadata_url(repo, package, version)
    return extract_info(fetch_json(url), package, version)
