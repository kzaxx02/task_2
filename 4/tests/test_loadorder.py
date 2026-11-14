"""Тесты порядка загрузки зависимостей."""

import unittest

from depgraph.graph import build_graph
from depgraph.loadorder import load_order


def order_for(table, root, substring=""):
    """Строит граф по словарю и возвращает порядок загрузки."""
    graph = build_graph(root, lambda name: table.get(name, []), substring)
    return load_order(graph)


class LoadOrderTests(unittest.TestCase):
    """Порядок: зависимости раньше зависимых пакетов."""

    def test_single_package(self):
        """Пакет без зависимостей загружается один."""
        self.assertEqual(order_for({"A": []}, "A"), ["A"])

    def test_chain(self):
        """Цепочка загружается с конца."""
        table = {"A": ["B"], "B": ["C"], "C": ["D"]}
        self.assertEqual(order_for(table, "A"), ["D", "C", "B", "A"])

    def test_diamond(self):
        """Общая зависимость загружается один раз и раньше остальных."""
        table = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        self.assertEqual(order_for(table, "A"), ["D", "B", "C", "A"])

    def test_independent_keep_declaration_order(self):
        """Независимые пакеты идут в порядке объявления."""
        table = {"A": ["C", "B"]}
        self.assertEqual(order_for(table, "A"), ["C", "B", "A"])

    def test_root_is_last(self):
        """Корневой пакет всегда последний."""
        table = {"A": ["B", "C"], "B": ["C"]}
        self.assertEqual(order_for(table, "A")[-1], "A")

    def test_cycle_is_broken(self):
        """Цикл не приводит к зависанию, все пакеты есть в порядке."""
        table = {"A": ["B"], "B": ["C"], "C": ["A", "D"]}
        order = order_for(table, "A")
        self.assertEqual(sorted(order), ["A", "B", "C", "D"])
        self.assertEqual(order, ["D", "C", "B", "A"])

    def test_self_loop(self):
        """Зависимость от самого себя пропускается."""
        self.assertEqual(order_for({"A": ["A", "B"]}, "A"), ["B", "A"])

    def test_filter_applied(self):
        """Отфильтрованные пакеты не входят в порядок."""
        table = {"A": ["XB", "C"], "XB": ["D"]}
        self.assertEqual(order_for(table, "A", "X"), ["C", "A"])

    def test_every_dependency_precedes_dependent(self):
        """Для графа без циклов каждая зависимость стоит раньше."""
        table = {"A": ["B", "C"], "B": ["D", "E"], "C": ["E"], "E": ["D"]}
        graph = build_graph("A", lambda name: table.get(name, []))
        position = {n: i for i, n in enumerate(load_order(graph))}
        for name, children in graph.edges.items():
            for child in children:
                self.assertLess(position[child], position[name])


if __name__ == "__main__":
    unittest.main()
