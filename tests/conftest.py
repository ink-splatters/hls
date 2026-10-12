"""Local manifest fixtures and an HTTP server for transport integration tests."""

import gzip
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture
def manifest_server(data_dir: Path) -> Iterator[tuple[str, list[dict[str, str]]]]:
    requests: list[dict[str, str]] = []

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, directory=str(data_dir), **kwargs)

        def do_GET(self) -> None:
            requests.append(dict(self.headers.items()))
            path = urlsplit(self.path).path
            if path.startswith("/redirect/"):
                self.send_response(302)
                self.send_header("Location", path.removeprefix("/redirect"))
                self.end_headers()
            elif path.startswith("/gzip/") or path == "/broken-gzip":
                body = (
                    b"invalid gzip"
                    if path == "/broken-gzip"
                    else gzip.compress((data_dir / path.removeprefix("/gzip/")).read_bytes())
                )
                self.send_response(200)
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()

        def log_message(self, format: str, *args) -> None:
            pass

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}", requests
        finally:
            server.shutdown()
            thread.join()
