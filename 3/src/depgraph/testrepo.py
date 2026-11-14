"""Чтение файла тестового репозитория.

Формат: по одной строке «A: B C» на пакет, где A — пакет, а B и C — его
прямые зависимости. Имена состоят из больших латинских букв. Пустые
строки и строки, начинающиеся с «#», игнорируются.
"""

import re

from depgraph.errors import FetchError

LINE_RE = re.compile(r"^(?P<name>[A-Z]+)\s*:(?P<deps>.*)$")
NAME_RE = re.compile(r"^[A-Z]+$")
COMMENT_PREFIX = "#"


def parse_line(line, number):
    """Разбирает строку описания пакета: возвращает (имя, зависимости)."""
    match = LINE_RE.match(line)
    if match is None:
        raise FetchError(f"строка {number}: ожидается формат 'A: B C'")
    dependencies = match.group("deps").split()
    for dependency in dependencies:
        if not NAME_RE.match(dependency):
            raise FetchError(
                f"строка {number}: недопустимое имя '{dependency}'"
            )
    return match.group("name"), dependencies


def parse_test_repo(text):
    """Разбирает текст тестового репозитория в словарь зависимостей."""
    table = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        name, dependencies = parse_line(line, number)
        if name in table:
            raise FetchError(f"строка {number}: пакет '{name}' описан дважды")
        table[name] = dependencies
    if not table:
        raise FetchError("файл тестового репозитория не содержит пакетов")
    return table


def load_test_repo(path):
    """Читает и разбирает файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as stream:
            text = stream.read()
    except (OSError, UnicodeDecodeError) as error:
        raise FetchError(f"не удалось прочитать '{path}': {error}") from error
    return parse_test_repo(text)
