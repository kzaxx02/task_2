"""Интерфейс командной строки."""

import argparse
import sys

from depgraph.config import LATEST_VERSION, build_config
from depgraph.errors import DepgraphError
from depgraph.graph import build_graph
from depgraph.loadorder import load_order
from depgraph.output import format_graph, format_load_order
from depgraph.sources import make_provider

EXIT_OK = 0
EXIT_ERROR = 2


def add_required_options(parser):
    """Добавляет обязательные опции: пакет и репозиторий."""
    parser.add_argument(
        "--package", required=True, help="имя анализируемого пакета"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="URL репозитория или путь к файлу тестового репозитория",
    )


def add_optional_options(parser):
    """Добавляет необязательные опции."""
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="работать с файлом тестового репозитория вместо URL",
    )
    parser.add_argument(
        "--version",
        default=LATEST_VERSION,
        help="версия пакета (по умолчанию: latest)",
    )
    parser.add_argument(
        "--ascii-tree",
        action="store_true",
        help="выводить зависимости в формате ASCII-дерева",
    )
    parser.add_argument(
        "--filter",
        default=None,
        help="не учитывать пакеты, имя которых содержит подстроку",
    )
    parser.add_argument(
        "--load-order",
        action="store_true",
        help="вывести порядок загрузки зависимостей пакета",
    )


def build_parser():
    """Создаёт разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Визуализация графа зависимостей пакетов Python.",
        allow_abbrev=False,
    )
    add_required_options(parser)
    add_optional_options(parser)
    return parser


def run(config):
    """Строит граф зависимостей и возвращает его текстовое описание."""
    provider = make_provider(config)
    graph = build_graph(config.package, provider, config.filter_substring)
    if config.load_order:
        return format_load_order(graph, load_order(graph))
    return format_graph(graph, config.filter_substring)


def main(argv=None):
    """Запускает приложение и возвращает код завершения."""
    args = build_parser().parse_args(argv)
    try:
        config = build_config(
            args.package,
            args.repo,
            args.test_mode,
            args.version,
            args.ascii_tree,
            args.filter,
            args.load_order,
        )
        report = run(config)
    except DepgraphError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(report)
    return EXIT_OK
