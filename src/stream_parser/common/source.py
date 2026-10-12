"""Read manifest bytes without interpreting their format."""

import gzip
from dataclasses import dataclass
from os import PathLike
from typing import TYPE_CHECKING, BinaryIO
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from collections.abc import Mapping

type Source = str | PathLike[str] | BinaryIO


@dataclass(frozen=True)
class SourceContent:
    """Manifest bytes and the final HTTP URL, if fetched remotely."""

    data: bytes
    url: str | None = None


def read_source(source: Source, *, headers: Mapping[str, str] | None = None) -> SourceContent:
    """Read a path, HTTP(S) URL, or binary stream.

    Caller-owned streams remain open. Files and HTTP responses opened here are
    closed before returning. I/O and decompression errors propagate unchanged.
    """
    if isinstance(source, str) and urlsplit(source).scheme in {"http", "https"}:
        request = Request(source, headers=dict(headers or {}))
        with urlopen(request) as response:
            data = response.read()
            if response.headers.get("Content-Encoding", "").strip().lower() == "gzip":
                data = gzip.decompress(data)
            return SourceContent(data, response.geturl())

    if isinstance(source, (str, PathLike)):
        with open(source, "rb") as stream:
            return SourceContent(stream.read())

    return SourceContent(source.read())
