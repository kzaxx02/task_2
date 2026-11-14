"""Тесты получения данных из репозитория."""

import socket
import unittest

from depgraph.errors import FetchError
from depgraph.fetcher import build_metadata_url, fetch_package_info
from fake_repo import FakeRepo


class UrlTests(unittest.TestCase):
    """Формирование URL."""

    def test_with_version(self):
        """URL для заданной версии."""
        url = build_metadata_url("https://pypi.org/", "demo", "1.0.0")
        self.assertEqual(url, "https://pypi.org/pypi/demo/1.0.0/json")

    def test_latest(self):
        """URL для последней версии."""
        url = build_metadata_url("https://pypi.org", "demo", "latest")
        self.assertEqual(url, "https://pypi.org/pypi/demo/json")


class FetchTests(unittest.TestCase):
    """Загрузка данных с тестового сервера."""

    @classmethod
    def setUpClass(cls):
        """Запускает тестовый репозиторий."""
        cls.repo = FakeRepo()
        cls.repo.start()

    @classmethod
    def tearDownClass(cls):
        """Останавливает тестовый репозиторий."""
        cls.repo.stop()

    def test_requested_version(self):
        """Возвращаются данные заданной версии."""
        info = fetch_package_info(self.repo.url, "demo", "1.0.0")
        self.assertEqual(info.version, "1.0.0")
        self.assertIn("alpha>=1.0", info.requires)

    def test_latest_version_is_resolved(self):
        """Для latest определяется конкретная версия."""
        info = fetch_package_info(self.repo.url, "demo", "latest")
        self.assertEqual(info.version, "2.0.0")

    def test_null_requires(self):
        """Отсутствие requires_dist означает пустой список."""
        info = fetch_package_info(self.repo.url, "empty", "1.0")
        self.assertEqual(info.requires, [])

    def test_not_found(self):
        """Неизвестный пакет вызывает ошибку."""
        with self.assertRaises(FetchError):
            fetch_package_info(self.repo.url, "missing", "1.0")

    def test_broken_json(self):
        """Некорректный JSON вызывает ошибку."""
        with self.assertRaises(FetchError):
            fetch_package_info(self.repo.url, "broken", "1.0")

    def test_missing_info(self):
        """Ответ без раздела info вызывает ошибку."""
        with self.assertRaises(FetchError):
            fetch_package_info(self.repo.url, "noinfo", "1.0")


class ConnectionTests(unittest.TestCase):
    """Недоступный репозиторий."""

    def test_connection_refused(self):
        """Закрытый порт вызывает FetchError."""
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with self.assertRaises(FetchError):
            fetch_package_info(f"http://127.0.0.1:{port}", "demo", "1.0.0")


if __name__ == "__main__":
    unittest.main()
