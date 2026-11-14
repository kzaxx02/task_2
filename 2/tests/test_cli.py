"""Тесты интерфейса командной строки."""

import contextlib
import io
import os
import unittest

from depgraph.cli import EXIT_ERROR, EXIT_OK, main
from fake_repo import FakeRepo

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

    @classmethod
    def setUpClass(cls):
        """Запускает тестовый репозиторий."""
        cls.repo = FakeRepo()
        cls.repo.start()

    @classmethod
    def tearDownClass(cls):
        """Останавливает тестовый репозиторий."""
        cls.repo.stop()

    def args(self, package, *extra):
        """Собирает аргументы запуска для тестового репозитория."""
        return ["--package", package, "--repo", self.repo.url, *extra]

    def test_prints_direct_dependencies(self):
        """Выводятся только прямые зависимости без дубликатов."""
        code, out, _ = run(self.args("demo", "--version", "1.0.0"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Прямые зависимости demo 1.0.0:", out)
        self.assertIn("- alpha >=1.0", out)
        self.assertIn("- beta-pkg <2,>=1", out)
        self.assertIn("- gamma >=3", out)
        self.assertNotIn("delta", out)
        self.assertEqual(out.count("alpha"), 1)

    def test_latest_version(self):
        """Версия latest заменяется найденной."""
        code, out, _ = run(self.args("demo"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("demo 2.0.0", out)

    def test_no_dependencies(self):
        """Пакет без зависимостей обрабатывается."""
        code, out, _ = run(self.args("empty", "--version", "1.0"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("прямых зависимостей нет", out)

    def test_package_not_found(self):
        """Несуществующий пакет даёт ошибку."""
        code, out, err = run(self.args("missing", "--version", "1.0"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("не найдены", err)

    def test_invalid_value_reports_error(self):
        """Ошибка значения даёт сообщение и код ошибки."""
        code, _, err = run(["--package", "x", "--repo", "bad"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка:", err)

    def test_test_mode_not_supported_yet(self):
        """Тестовый режим пока недоступен."""
        code, _, err = run(
            ["--package", "A", "--repo", DATA, "--test-mode"]
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("этапе 3", err)

    def test_missing_required(self):
        """Отсутствие обязательных параметров даёт код ошибки."""
        code, _, err = run(["--package", "x"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("--repo", err)


if __name__ == "__main__":
    unittest.main()
