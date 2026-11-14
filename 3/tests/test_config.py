"""Тесты проверки параметров конфигурации."""

import os
import unittest

from depgraph import config as cfg

DATA = os.path.join(os.path.dirname(__file__), "data", "test_repo.txt")
URL = "https://pypi.org/simple/"


class PackageTests(unittest.TestCase):
    """Проверка имени пакета."""

    def test_valid_name(self):
        """Корректное имя принимается."""
        self.assertEqual(cfg.validate_package("requests", False), "requests")

    def test_empty_name(self):
        """Пустое имя вызывает ошибку."""
        with self.assertRaises(cfg.ConfigError):
            cfg.validate_package("  ", False)

    def test_bad_chars(self):
        """Недопустимые символы вызывают ошибку."""
        with self.assertRaises(cfg.ConfigError):
            cfg.validate_package("bad name!", False)

    def test_test_mode_uppercase_only(self):
        """В тестовом режиме допустимы только большие буквы."""
        self.assertEqual(cfg.validate_package("AB", True), "AB")
        with self.assertRaises(cfg.ConfigError):
            cfg.validate_package("ab1", True)


class RepoTests(unittest.TestCase):
    """Проверка адреса репозитория."""

    def test_valid_url(self):
        """Корректный URL принимается."""
        self.assertEqual(cfg.validate_repo(URL, False), URL)

    def test_bad_url(self):
        """Некорректный URL вызывает ошибку."""
        for bad in ("pypi.org", "ftp://x.org", "http://"):
            with self.assertRaises(cfg.ConfigError):
                cfg.validate_repo(bad, False)

    def test_existing_file(self):
        """Существующий файл принимается в тестовом режиме."""
        self.assertEqual(cfg.validate_repo(DATA, True), DATA)

    def test_missing_file(self):
        """Отсутствующий файл вызывает ошибку."""
        with self.assertRaises(cfg.ConfigError):
            cfg.validate_repo("no/such/file.txt", True)

    def test_directory_instead_of_file(self):
        """Каталог вместо файла вызывает ошибку."""
        with self.assertRaises(cfg.ConfigError):
            cfg.validate_repo(os.path.dirname(DATA), True)


class VersionAndFilterTests(unittest.TestCase):
    """Проверка версии и подстроки фильтра."""

    def test_versions(self):
        """Корректные версии принимаются, некорректные нет."""
        for good in ("1", "1.2.3", "2.0rc1", "latest"):
            self.assertEqual(cfg.validate_version(good), good)
        for bad in ("", "v1", "1..2", "abc"):
            with self.assertRaises(cfg.ConfigError):
                cfg.validate_version(bad)

    def test_filter(self):
        """Фильтр: значение по умолчанию и ошибки."""
        self.assertEqual(cfg.validate_filter(None), "")
        self.assertEqual(cfg.validate_filter("test"), "test")
        for bad in ("", "a b"):
            with self.assertRaises(cfg.ConfigError):
                cfg.validate_filter(bad)


if __name__ == "__main__":
    unittest.main()
