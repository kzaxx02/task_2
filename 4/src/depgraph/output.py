"""Форматирование результатов для вывода на экран."""

NO_DEPENDENCIES = "(нет зависимостей)"
ARROW = " -> "


def format_edge(name, dependencies):
    """Форматирует строку графа: пакет и его прямые зависимости."""
    shown = ", ".join(dependencies) if dependencies else NO_DEPENDENCIES
    return f"  {name}{ARROW}{shown}"


def format_cycles(cycles):
    """Форматирует раздел с циклическими зависимостями."""
    if not cycles:
        return ["Циклических зависимостей нет."]
    lines = ["Обнаружены циклические зависимости:"]
    for cycle in cycles:
        lines.append(f"  {ARROW.join(cycle)}")
    return lines


def format_graph(graph, substring):
    """Форматирует граф зависимостей для вывода на экран."""
    lines = [f"Граф зависимостей пакета {graph.root}:"]
    if substring:
        lines.append(f"(пакеты, содержащие '{substring}', не учитываются)")
    for name, dependencies in graph.edges.items():
        lines.append(format_edge(name, dependencies))
    lines.append(f"Пакетов в графе: {len(graph.edges)}")
    lines.extend(format_cycles(graph.cycles))
    return "\n".join(lines)


def format_load_order(graph, order):
    """Форматирует порядок загрузки пакетов (зависимости идут первыми)."""
    lines = [f"Порядок загрузки зависимостей пакета {graph.root}:"]
    for number, name in enumerate(order, start=1):
        lines.append(f"  {number}. {name}")
    if graph.cycles:
        lines.append("Циклы разорваны, порядок для них условный:")
        lines.extend(format_cycles(graph.cycles)[1:])
    return "\n".join(lines)
