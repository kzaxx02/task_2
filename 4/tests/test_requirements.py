"""Тесты разбора зависимостей."""

import unittest

from depgraph.errors import RequirementError
from depgraph.requirements import (
    Dependency,
    collect_direct_dependencies,
    parse_requirement,
)


class ParseTests(unittest.TestCase):
    """Разбор одной строки зависимости."""

    def test_simple_name(self):
        """Имя без ограничений."""
        self.assertEqual(parse_requirement("idna"), Dependency("idna", ""))

    def test_specifier_without_parens(self):
        """Ограничение версии без скобок."""
        dep = parse_requirement("urllib3<3,>=1.21.1")
        self.assertEqual(dep, Dependency("urllib3", "<3,>=1.21.1"))

    def test_specifier_in_parens_and_normalized_name(self):
        """Скобки снимаются, имя нормализуется."""
        dep = parse_requirement("Beta_Pkg (>=1.0)")
        self.assertEqual(dep, Dependency("beta-pkg", ">=1.0"))

    def test_extras_of_dependency_are_dropped(self):
        """Дополнения в квадратных скобках не входят в имя."""
        dep = parse_requirement("gamma[socks]>=1")
        self.assertEqual(dep, Dependency("gamma", ">=1"))

    def test_environment_marker_is_kept(self):
        """Маркер окружения не отменяет зависимость."""
        dep = parse_requirement("tomli; python_version < '3.11'")
        self.assertEqual(dep, Dependency("tomli", ""))

    def test_extra_marker_is_skipped(self):
        """Необязательная зависимость пропускается."""
        self.assertIsNone(parse_requirement("pytest; extra == 'test'"))

    def test_invalid_line(self):
        """Некорректная строка вызывает ошибку."""
        with self.assertRaises(RequirementError):
            parse_requirement(">=1.0")


class CollectTests(unittest.TestCase):
    """Сбор списка прямых зависимостей."""

    def test_duplicates_and_extras(self):
        """Дубликаты удаляются, extras пропускаются, порядок сохраняется."""
        lines = ["b>=1", "a", "c; extra == 'x'", "B<3"]
        names = [dep.name for dep in collect_direct_dependencies(lines)]
        self.assertEqual(names, ["b", "a"])

    def test_empty(self):
        """Пустой список даёт пустой результат."""
        self.assertEqual(collect_direct_dependencies([]), [])


if __name__ == "__main__":
    unittest.main()
