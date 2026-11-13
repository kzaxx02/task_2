"""Тесты интерфейса командной строки."""

import contextlib
import io
import os
import unittest

from depgraph.cli import EXIT_ERROR, EXIT_OK, main

DATA = os.path.join(os.path.dirname(__file__), "data", "test_repo.txt")


def run(argv):
    """Запускает main и возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exit_info:
            code = exit_info.code
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    """Проверка запуска приложения."""

    def test_prints_all_parameters(self):
        """Все параметры выводятся в формате ключ-значение."""
        code, out, _ = run(
            ["--package", "requests", "--repo", "https://pypi.org/",
             "--version", "2.31.0", "--ascii-tree", "--filter", "test"]
        )
        self.assertEqual(code, EXIT_OK)
        for line in ("package: requests", "version: 2.31.0",
                     "ascii_tree: true", "filter: test",
                     "test_mode: false", "repo: https://pypi.org/"):
            self.assertIn(line, out)

    def test_test_mode(self):
        """Тестовый режим с файлом работает."""
        code, out, _ = run(
            ["--package", "A", "--repo", DATA, "--test-mode"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertIn("test_mode: true", out)

    def test_invalid_value_reports_error(self):
        """Ошибка значения даёт сообщение и код ошибки."""
        code, out, err = run(["--package", "x", "--repo", "bad"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка:", err)

    def test_missing_required(self):
        """Отсутствие обязательных параметров даёт код ошибки."""
        code, _, err = run(["--package", "x"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("--repo", err)


if __name__ == "__main__":
    unittest.main()
