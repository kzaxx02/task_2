"""Тесты чтения файла тестового репозитория."""

import os
import tempfile
import unittest

from depgraph.errors import FetchError
from depgraph.testrepo import load_test_repo, parse_test_repo


class ParseTests(unittest.TestCase):
    """Разбор текста."""

    def test_valid(self):
        """Корректный текст с пустыми строками и комментариями."""
        text = "# заметка\n\nA: B C\nB:\nC :\n"
        table = parse_test_repo(text)
        self.assertEqual(table, {"A": ["B", "C"], "B": [], "C": []})

    def test_bad_format(self):
        """Строка без двоеточия вызывает ошибку."""
        with self.assertRaises(FetchError):
            parse_test_repo("A B C\n")

    def test_bad_names(self):
        """Имена не из больших латинских букв вызывают ошибку."""
        for text in ("a: B\n", "A: b\n", "A1: B\n", "A: B1\n"):
            with self.assertRaises(FetchError):
                parse_test_repo(text)

    def test_duplicate(self):
        """Повторное описание пакета вызывает ошибку."""
        with self.assertRaises(FetchError):
            parse_test_repo("A: B\nA: C\n")

    def test_empty(self):
        """Файл без пакетов вызывает ошибку."""
        with self.assertRaises(FetchError):
            parse_test_repo("# только комментарий\n\n")

    def test_error_mentions_line_number(self):
        """Сообщение об ошибке содержит номер строки."""
        with self.assertRaises(FetchError) as context:
            parse_test_repo("A: B\nbad\n")
        self.assertIn("строка 2", str(context.exception))


class LoadTests(unittest.TestCase):
    """Чтение файла."""

    def test_load(self):
        """Файл читается и разбирается."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "repo.txt")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("A: B\n")
            self.assertEqual(load_test_repo(path), {"A": ["B"]})

    def test_missing_file(self):
        """Отсутствующий файл вызывает ошибку."""
        with self.assertRaises(FetchError):
            load_test_repo("no/such/file.txt")

    def test_not_utf8(self):
        """Файл не в UTF-8 вызывает ошибку."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "repo.txt")
            with open(path, "wb") as stream:
                stream.write(b"\xff\xfe\x00")
            with self.assertRaises(FetchError):
                load_test_repo(path)


if __name__ == "__main__":
    unittest.main()
