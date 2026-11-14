"""Тесты вспомогательных функций сравнения с pip."""

import tempfile
import unittest
import zipfile
from pathlib import Path

import compare_with_pip as cmp


class HelperTests(unittest.TestCase):
    """Проверка функций, не запускающих pip."""

    def test_all_names_includes_referenced(self):
        """В список попадают и только упомянутые пакеты."""
        table = {"A": ["B"]}
        self.assertEqual(cmp.all_names(table), ["A", "B"])

    def test_parse_pip_order(self):
        """Порядок извлекается из вывода pip."""
        output = "x\nInstalling collected packages: d, c, a\ny\n"
        self.assertEqual(cmp.parse_pip_order(output), ["D", "C", "A"])

    def test_parse_pip_order_missing(self):
        """Отсутствие строки с порядком вызывает завершение."""
        with self.assertRaises(SystemExit):
            cmp.parse_pip_order("nothing here")

    def test_count_violations(self):
        """Подсчёт рёбер, нарушающих порядок."""
        edges = {"A": ["B"], "B": []}
        self.assertEqual(cmp.count_violations(["B", "A"], edges), 0)
        self.assertEqual(cmp.count_violations(["A", "B"], edges), 1)

    def test_wheel_contains_requirements(self):
        """Созданный wheel содержит зависимости в METADATA."""
        with tempfile.TemporaryDirectory() as folder:
            cmp.write_wheel(folder, "A", ["B", "C"])
            path = Path(folder) / "a-1.0-py3-none-any.whl"
            with zipfile.ZipFile(path) as archive:
                text = archive.read("a-1.0.dist-info/METADATA").decode()
        self.assertIn("Requires-Dist: B", text)
        self.assertIn("Requires-Dist: C", text)


if __name__ == "__main__":
    unittest.main()
