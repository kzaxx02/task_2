#!/bin/sh
# Запуск приложения: ./run.sh --package NAME --repo URL [опции]
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src" exec python3 -m depgraph "$@"
