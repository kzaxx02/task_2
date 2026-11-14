"""Форматирование результатов для вывода на экран."""

NO_DEPENDENCIES = "(прямых зависимостей нет)"


def format_dependency(dependency):
    """Форматирует одну зависимость: имя и ограничение версии."""
    if dependency.specifier:
        return f"{dependency.name} {dependency.specifier}"
    return dependency.name


def format_dependencies(info, dependencies):
    """Форматирует список прямых зависимостей пакета."""
    lines = [f"Прямые зависимости {info.package} {info.version}:"]
    if not dependencies:
        lines.append(f"  {NO_DEPENDENCIES}")
    for dependency in dependencies:
        lines.append(f"  - {format_dependency(dependency)}")
    return "\n".join(lines)
