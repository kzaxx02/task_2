"""Тесты построения графа зависимостей."""

import unittest

from depgraph.errors import ConfigError, DepgraphError
from depgraph.graph import build_graph


def provider(table):
    """Создаёт функцию получения зависимостей по словарю."""
    return lambda name: table.get(name, [])


class BuildTests(unittest.TestCase):
    """Обход графа и обработка циклов."""

    def test_chain(self):
        """Транзитивные зависимости попадают в граф."""
        graph = build_graph("A", provider({"A": ["B"], "B": ["C"]}))
        self.assertEqual(graph.edges, {"A": ["B"], "B": ["C"], "C": []})
        self.assertEqual(graph.cycles, [])

    def test_diamond_visits_shared_once(self):
        """Общая зависимость обходится один раз."""
        table = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        graph = build_graph("A", provider(table))
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C"])
        self.assertEqual(graph.edges["C"], ["D"])

    def test_cycle(self):
        """Цикл обнаруживается, обход завершается."""
        table = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_graph("A", provider(table))
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])

    def test_self_loop(self):
        """Зависимость пакета от самого себя считается циклом."""
        graph = build_graph("A", provider({"A": ["A", "B"]}))
        self.assertEqual(graph.cycles, [["A", "A"]])
        self.assertIn("B", graph.edges)

    def test_duplicates_removed(self):
        """Повторы в списке зависимостей удаляются."""
        graph = build_graph("A", provider({"A": ["B", "B"]}))
        self.assertEqual(graph.edges["A"], ["B"])


class FilterTests(unittest.TestCase):
    """Фильтрация пакетов по подстроке."""

    def test_filtered_package_and_subtree_excluded(self):
        """Пакет с подстрокой и его ветка не учитываются."""
        table = {"A": ["XB", "C"], "XB": ["D"], "C": []}
        graph = build_graph("A", provider(table), "X")
        self.assertEqual(graph.edges, {"A": ["C"], "C": []})

    def test_shared_dependency_still_reachable(self):
        """Зависимость остаётся, если достижима другим путём."""
        table = {"A": ["XB", "C"], "XB": ["D"], "C": ["D"]}
        graph = build_graph("A", provider(table), "X")
        self.assertIn("D", graph.edges)

    def test_empty_substring_filters_nothing(self):
        """Пустая подстрока ничего не исключает."""
        graph = build_graph("A", provider({"A": ["B"]}), "")
        self.assertIn("B", graph.edges)

    def test_root_excluded(self):
        """Корневой пакет, исключённый фильтром, вызывает ошибку."""
        with self.assertRaises(ConfigError):
            build_graph("AB", provider({}), "B")


class DepthTests(unittest.TestCase):
    """Слишком глубокие цепочки."""

    def test_recursion_limit_reported(self):
        """Переполнение рекурсии превращается в понятную ошибку."""
        def endless(name):
            """Каждый пакет зависит от нового пакета."""
            return [name + "x"]

        with self.assertRaises(DepgraphError):
            build_graph("a", endless)


if __name__ == "__main__":
    unittest.main()
