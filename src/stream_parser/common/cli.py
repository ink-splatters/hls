"""Click input conventions and error presentation shared by both commands."""

import sys
import zlib
from contextlib import contextmanager
from http.client import HTTPException
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import click

if TYPE_CHECKING:
    from collections.abc import Generator

    from .source import Source


def parse_headers(
    ctx: click.Context, param: click.Parameter, values: tuple[str, ...]
) -> dict[str, str]:
    """Convert repeated curl-style headers into request headers."""
    headers: dict[str, str] = {}
    for value in values:
        name, separator, content = value.partition(":")
        if not separator or not name.strip():
            raise click.BadParameter("expected 'Name: value'", ctx=ctx, param=param)
        headers[name.strip()] = content.strip()
    return headers


def source_options() -> list[click.Option]:
    """Create independent parameter objects for each command."""
    return [
        click.Option(
            ["-f", "--file"],
            type=click.Path(exists=True, dir_okay=False, allow_dash=True),
            help="Manifest path. Use '-' for stdin (default).",
        ),
        click.Option(
            ["-u", "--url"],
            help="HTTP(S) manifest URL. Use '-' to read a URL from stdin.",
        ),
        click.Option(
            ["-H", "--headers"],
            multiple=True,
            callback=parse_headers,
            help="HTTP header in 'Name: value' form. May be repeated.",
        ),
    ]


def input_source(file: str | None, url: str | None) -> Source:
    """Resolve CLI sentinels; library callers pass paths, URLs, or streams."""
    if file is not None and url is not None:
        raise click.UsageError("--file and --url are mutually exclusive")
    if url is not None:
        if url == "-":
            url = sys.stdin.read().strip()
        if urlsplit(url).scheme not in {"http", "https"}:
            raise click.BadParameter("expected an HTTP(S) URL", param_hint="--url")
        return url
    if file is None or file == "-":
        return sys.stdin.buffer
    return Path(file)


@contextmanager
def report_errors() -> Generator[None]:
    """Render expected input, transport, and protocol errors at the CLI boundary."""
    try:
        yield
    except (OSError, ValueError, HTTPException, EOFError, zlib.error) as error:
        raise click.ClickException(str(error)) from error
