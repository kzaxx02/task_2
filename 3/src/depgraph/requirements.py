"""Разбор строк зависимостей в формате PEP 508."""

import re
from dataclasses import dataclass

from depgraph.errors import RequirementError

NAME_SEPARATORS_RE = re.compile(r"[-_.]+")
REQUIREMENT_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*"
    r"(?:\[[^\]]*\])?\s*"
    r"(?P<spec>[^;]*)"
    r"(?:;(?P<marker>.*))?$"
)
EXTRA_MARKER_RE = re.compile(r"\bextra\s*==")


@dataclass(frozen=True)
class Dependency:
    """Прямая зависимость: нормализованное имя и ограничение версии."""

    name: str
    specifier: str


def normalize_name(name):
    """Приводит имя пакета к нормальной форме (PEP 503)."""
    return NAME_SEPARATORS_RE.sub("-", name).lower()


def parse_requirement(text):
    """Разбирает строку зависимости.

    Возвращает Dependency или None, если зависимость относится
    к необязательной группе (маркер extra) и не является прямой.
    """
    match = REQUIREMENT_RE.match(text)
    if match is None:
        raise RequirementError(f"не удалось разобрать зависимость '{text}'")
    marker = match.group("marker") or ""
    if EXTRA_MARKER_RE.search(marker):
        return None
    specifier = match.group("spec").strip().strip("()").strip()
    return Dependency(normalize_name(match.group("name")), specifier)


def collect_direct_dependencies(lines):
    """Возвращает список уникальных прямых зависимостей по строкам."""
    found = {}
    for line in lines:
        dependency = parse_requirement(line)
        if dependency is not None and dependency.name not in found:
            found[dependency.name] = dependency
    return list(found.values())
