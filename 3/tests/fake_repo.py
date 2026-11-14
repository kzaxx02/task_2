"""Локальный HTTP-сервер, имитирующий JSON API репозитория PyPI."""

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEMO_REQUIRES = [
    "alpha>=1.0",
    "Beta_Pkg (<2,>=1) ; python_version >= '3.8'",
    "gamma[extra1]>=3",
    "delta ; extra == 'dev'",
    "alpha>=1.0",
]


def make_body(version, requires):
    """Формирует JSON-ответ в формате PyPI."""
    info = {"version": version, "requires_dist": requires}
    return json.dumps({"info": info}).encode("utf-8")


ROUTES = {
    "/pypi/demo/1.0.0/json": make_body("1.0.0", DEMO_REQUIRES),
    "/pypi/demo/json": make_body("2.0.0", ["alpha"]),
    "/pypi/alpha/json": make_body("1.0", ["gamma"]),
    "/pypi/beta-pkg/json": make_body("1.5", ["alpha", "gamma"]),
    "/pypi/gamma/json": make_body("3.0", None),
    "/pypi/cyca/json": make_body("1.0", ["cycb"]),
    "/pypi/cycb/json": make_body("1.0", ["cyca"]),
    "/pypi/empty/1.0/json": make_body("1.0", None),
    "/pypi/broken/1.0/json": b"not a json",
    "/pypi/noinfo/1.0/json": b"{}",
}


class Handler(BaseHTTPRequestHandler):
    """Обработчик запросов тестового репозитория."""

    def do_GET(self):
        """Отвечает на GET-запрос по таблице ROUTES."""
        body = ROUTES.get(self.path)
        status = HTTPStatus.OK if body else HTTPStatus.NOT_FOUND
        self.send_response(status)
        self.end_headers()
        self.wfile.write(body or b"")

    def log_message(self, *args):
        """Отключает вывод журнала запросов."""


class FakeRepo:
    """Запускает и останавливает тестовый сервер в отдельном потоке."""

    def __init__(self):
        """Создаёт сервер на свободном порту localhost."""
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever)

    @property
    def url(self):
        """Базовый URL запущенного сервера."""
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def start(self):
        """Запускает сервер."""
        self.thread.start()

    def stop(self):
        """Останавливает сервер."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
