"""Порядок загрузки зависимостей: сначала зависимости, потом пакет."""

from depgraph.errors import DepgraphError


def load_order(graph):
    """Возвращает порядок загрузки пакетов графа.

    Выполняется рекурсивный обход в глубину с выдачей пакета после
    всех его зависимостей (обратный порядок завершения). Корневой пакет
    оказывается последним. Рёбра, замыкающие цикл, пропускаются:
    так цикл разрывается в точке, где обход возвращается к пакету
    из текущей цепочки.
    """
    order = []
    visited = set()

    def visit(name):
        """Обходит зависимости пакета и добавляет пакет в порядок."""
        visited.add(name)
        for child in graph.edges[name]:
            if child not in visited:
                visit(child)
        order.append(name)

    try:
        visit(graph.root)
    except RecursionError as error:
        raise DepgraphError(
            "слишком глубокая цепочка зависимостей"
        ) from error
    return order
