"""Тесты интерфейса командной строки."""

import contextlib
import io
import os
import unittest

from depgraph.cli import EXIT_ERROR, EXIT_OK, main
from fake_repo import FakeRepo

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def data(name):
    """Возвращает путь к файлу тестового репозитория."""
    return os.path.join(DATA_DIR, name)


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

    def test_transitive_graph(self):
        """Строится граф с транзитивными зависимостями без extras."""
        code, out, _ = run(self.args("demo", "--version", "1.0.0"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("demo -> alpha, beta-pkg, gamma", out)
        self.assertIn("alpha -> gamma", out)
        self.assertIn("beta-pkg -> alpha, gamma", out)
        self.assertIn("gamma -> (нет зависимостей)", out)
        self.assertNotIn("delta", out)
        self.assertIn("Циклических зависимостей нет.", out)

    def test_filter_in_real_mode(self):
        """Фильтр исключает пакеты по подстроке."""
        code, out, _ = run(
            self.args("demo", "--version", "1.0.0", "--filter", "beta")
        )
        self.assertEqual(code, EXIT_OK)
        self.assertNotIn("beta-pkg", out.split("\n", 2)[2])
        self.assertIn("demo -> alpha, gamma", out)

    def test_real_mode_cycle(self):
        """Цикл в реальном репозитории не вызывает зависания."""
        code, out, _ = run(self.args("cyca"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("cyca -> cycb -> cyca", out)

    def test_latest_version(self):
        """Для корневого пакета при latest используется последняя версия."""
        code, out, _ = run(self.args("demo"))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("demo -> alpha", out)

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

    def test_test_mode_diamond(self):
        """Тестовый режим: общий узел выводится один раз."""
        code, out, _ = run(
            ["--package", "A", "--repo", data("diamond.txt"), "--test-mode"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertIn("A -> B, C", out)
        self.assertEqual(out.count("D ->"), 1)
        self.assertIn("Пакетов в графе: 4", out)

    def test_test_mode_cycle(self):
        """Тестовый режим: цикл выводится в отдельном разделе."""
        code, out, _ = run(
            ["--package", "A", "--repo", data("cycle.txt"), "--test-mode"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertIn("A -> B -> C -> A", out)

    def test_test_mode_filter(self):
        """Тестовый режим: фильтр убирает пакет и его ветку."""
        code, out, _ = run(
            ["--package", "A", "--repo", data("filter.txt"),
             "--test-mode", "--filter", "B"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertNotIn("AB", out)

    def test_test_mode_unknown_root(self):
        """Тестовый режим: неописанный корневой пакет даёт ошибку."""
        code, _, err = run(
            ["--package", "Z", "--repo", data("chain.txt"), "--test-mode"]
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не описан", err)

    def test_root_excluded_by_filter(self):
        """Корневой пакет, исключённый фильтром, даёт ошибку."""
        code, _, err = run(
            ["--package", "AB", "--repo", data("filter.txt"),
             "--test-mode", "--filter", "B"]
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("исключён", err)

    def test_load_order_test_mode(self):
        """Режим --load-order выводит порядок с зависимостями впереди."""
        code, out, _ = run(
            ["--package", "A", "--repo", data("diamond.txt"),
             "--test-mode", "--load-order"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Порядок загрузки зависимостей пакета A:", out)
        self.assertIn("1. D", out)
        self.assertIn("4. A", out)
        self.assertNotIn("Пакетов в графе", out)

    def test_load_order_cycle_note(self):
        """При циклах выводится пометка о разрыве цикла."""
        code, out, _ = run(
            ["--package", "A", "--repo", data("cycle.txt"),
             "--test-mode", "--load-order"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Циклы разорваны", out)
        self.assertIn("A -> B -> C -> A", out)

    def test_load_order_with_filter(self):
        """Порядок загрузки учитывает фильтр."""
        code, out, _ = run(
            ["--package", "A", "--repo", data("filter.txt"),
             "--test-mode", "--load-order", "--filter", "B"]
        )
        self.assertEqual(code, EXIT_OK)
        self.assertNotIn("AB", out)

    def test_load_order_real_mode(self):
        """Порядок загрузки работает и для репозитория по URL."""
        code, out, _ = run(
            self.args("demo", "--version", "1.0.0", "--load-order")
        )
        self.assertEqual(code, EXIT_OK)
        self.assertIn("1. gamma", out)
        self.assertIn("2. alpha", out)
        self.assertIn("3. beta-pkg", out)
        self.assertIn("4. demo", out)

    def test_missing_required(self):
        """Отсутствие обязательных параметров даёт код ошибки."""
        code, _, err = run(["--package", "x"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("--repo", err)


if __name__ == "__main__":
    unittest.main()
