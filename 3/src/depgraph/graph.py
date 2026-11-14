"""Построение графа зависимостей алгоритмом DFS с рекурсией."""

from dataclasses import dataclass

from depgraph.errors import ConfigError, DepgraphError


@dataclass(frozen=True)
class DependencyGraph:
    """Граф зависимостей.

    edges: словарь «пакет -> список прямых зависимостей» в порядке
    обхода DFS; cycles: найденные циклы, каждый как список имён,
    в котором первый и последний элементы совпадают.
    """

    root: str
    edges: dict
    cycles: list


class GraphBuilder:
    """Строит граф зависимостей рекурсивным обходом в глубину."""

    def __init__(self, get_dependencies, substring):
        """Принимает функцию «имя -> список имён» и подстроку фильтра."""
        self.get_dependencies = get_dependencies
        self.substring = substring
        self.edges = {}
        self.cycles = []

    def is_excluded(self, name):
        """Проверяет, что имя содержит подстроку фильтра."""
        return bool(self.substring) and self.substring in name

    def build(self, root):
        """Строит граф, начиная с корневого пакета."""
        if self.is_excluded(root):
            raise ConfigError(
                f"пакет '{root}' исключён фильтром '{self.substring}'"
            )
        try:
            self.visit(root, [])
        except RecursionError as error:
            raise DepgraphError(
                "слишком глубокая цепочка зависимостей"
            ) from error
        return DependencyGraph(root, self.edges, self.cycles)

    def visit(self, name, path):
        """Рекурсивно обходит зависимости пакета.

        path — пакеты текущей цепочки рекурсии; повторная встреча
        пакета из path означает цикл.
        """
        found = self.get_dependencies(name)
        children = [dep for dep in found if not self.is_excluded(dep)]
        self.edges[name] = list(dict.fromkeys(children))
        path.append(name)
        for child in self.edges[name]:
            if child in path:
                self.cycles.append(path[path.index(child):] + [child])
            elif child not in self.edges:
                self.visit(child, path)
        path.pop()


def build_graph(root, get_dependencies, substring=""):
    """Строит граф зависимостей пакета root."""
    return GraphBuilder(get_dependencies, substring).build(root)
