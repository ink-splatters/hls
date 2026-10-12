"""HLS operations on the m3u8 playlist model."""

from itertools import chain
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import m3u8

from stream_parser.common.source import read_source

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from stream_parser.common.source import Source


class InvalidPlaylistError(ValueError):
    """The input cannot be read as an HLS playlist."""


def load(source: Source, *, headers: Mapping[str, str] | None = None) -> m3u8.M3U8:
    """Load a path, HTTP(S) URL, or binary stream as a UTF-8 HLS playlist."""
    content = read_source(source, headers=headers)
    try:
        text = content.data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidPlaylistError("invalid UTF-8") from error
    if text.partition("\n")[0].rstrip("\r") != "#EXTM3U":
        raise InvalidPlaylistError("missing #EXTM3U header")
    try:
        return m3u8.loads(text, uri=content.url)
    except ValueError as error:
        raise InvalidPlaylistError("invalid playlist") from error


def iter_segment_urls(playlist: m3u8.M3U8, base_url: str | None = None) -> Iterator[str]:
    """Yield initialization URLs followed by media URLs without fetching children.

    By default, remote references resolve against the final response URL and
    local references stay relative. An override is a directory URL; an empty
    override leaves references relative. Byte-range resources retain repeats.
    """
    base = playlist.base_uri if base_url is None else base_url
    if base:
        base = f"{base.rstrip('/')}/"
    for segment in chain(playlist.segment_map, playlist.segments):
        if segment is not None and segment.uri:
            yield urljoin(base or "", segment.uri)


def dumps(playlist: m3u8.M3U8) -> str:
    """Serialize a parsed playlist as M3U8 text."""
    return playlist.dumps()
