"""Сравнение порядка загрузки depgraph с порядком установки pip.

Скрипт нужен только для проверки результатов (этап 4): pip здесь не
используется для получения зависимостей приложением. По файлу тестового
репозитория создаются пустые wheel-пакеты, pip устанавливает корневой
пакет из этой папки без доступа к сети, а порядок установки берётся из
строки «Installing collected packages» его вывода.

Запуск: PYTHONPATH=src python3 scripts/compare_with_pip.py FILE PACKAGE
"""

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from depgraph.graph import build_graph
from depgraph.loadorder import load_order
from depgraph.sources import FileRepoProvider
from depgraph.testrepo import load_test_repo

PIP_MARKER = "Installing collected packages: "
VERSION = "1.0"
WHEEL_TEXT = (
    "Wheel-Version: 1.0\nGenerator: depgraph\n"
    "Root-Is-Purelib: true\nTag: py3-none-any\n"
)


def all_names(table):
    """Возвращает имена всех пакетов, включая только упомянутые."""
    names = set(table)
    for dependencies in table.values():
        names.update(dependencies)
    return sorted(names)


def write_wheel(folder, name, dependencies):
    """Создаёт пустой wheel-пакет с заданными зависимостями."""
    lower = name.lower()
    info = f"{lower}-{VERSION}.dist-info"
    requires = "".join(f"Requires-Dist: {dep}\n" for dep in dependencies)
    metadata = f"Metadata-Version: 2.1\nName: {lower}\n"
    metadata += f"Version: {VERSION}\n{requires}"
    record = "".join(f"{info}/{item},,\n" for item in ("METADATA", "WHEEL"))
    record += f"{info}/RECORD,,\n"
    path = Path(folder) / f"{lower}-{VERSION}-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{info}/METADATA", metadata)
        archive.writestr(f"{info}/WHEEL", WHEEL_TEXT)
        archive.writestr(f"{info}/RECORD", record)


def write_repo(table, folder):
    """Создаёт wheel-пакеты для всех пакетов тестового репозитория."""
    for name in all_names(table):
        write_wheel(folder, name, table.get(name, []))


def parse_pip_order(output):
    """Извлекает порядок установки из вывода pip (имена заглавными)."""
    for line in output.splitlines():
        if line.startswith(PIP_MARKER):
            names = line[len(PIP_MARKER):].split(", ")
            return [name.strip().upper() for name in names]
    raise SystemExit(f"pip не вывел порядок установки:\n{output}")


def run_pip(table, root):
    """Устанавливает root через pip и возвращает порядок установки."""
    with tempfile.TemporaryDirectory() as folder:
        write_repo(table, folder)
        command = [
            sys.executable, "-m", "pip", "install", "--no-index",
            "--find-links", folder, "--target", f"{folder}/site",
            "--no-cache-dir", "--disable-pip-version-check", root.lower(),
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
    return parse_pip_order(result.stdout + result.stderr)


def count_violations(order, edges):
    """Считает рёбра «пакет -> зависимость», где зависимость стоит позже."""
    position = {name: index for index, name in enumerate(order)}
    return sum(
        1
        for name, children in edges.items()
        for child in children
        if position[child] > position[name]
    )


def format_row(label, order, edges):
    """Форматирует строку сравнения для одного порядка."""
    violations = count_violations(order, edges)
    return f"{label:<8}: {', '.join(order)}  (нарушений: {violations})"


def compare(table, root):
    """Возвращает текст сравнения порядков depgraph и pip."""
    graph = build_graph(root, FileRepoProvider(table, root))
    ours = load_order(graph)
    pip_order = run_pip(table, root)
    verdict = "совпадают" if ours == pip_order else "различаются"
    return "\n".join([
        format_row("depgraph", ours, graph.edges),
        format_row("pip", pip_order, graph.edges),
        f"Порядки {verdict}.",
    ])


def main(argv=None):
    """Точка входа скрипта."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo_file", help="файл тестового репозитория")
    parser.add_argument("package", help="корневой пакет (большие буквы)")
    args = parser.parse_args(argv)
    table = load_test_repo(args.repo_file)
    print(compare(table, args.package))


if __name__ == "__main__":
    main()
