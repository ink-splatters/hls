"""DASH operations on mpd-parser's manifest and segment models."""

from typing import TYPE_CHECKING

from lxml import etree
from mpd_parser.models.composite_tags import MPD
from mpd_parser.parser import Parser

from stream_parser.common.source import read_source

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from datetime import datetime

    from stream_parser.common.source import Source


class InvalidManifestError(ValueError):
    """The input cannot be read as an MPD document."""


def load(source: Source, *, headers: Mapping[str, str] | None = None) -> MPD:
    """Load a path, HTTP(S) URL, or binary stream, honoring XML encoding."""
    content = read_source(source, headers=headers)
    parser = etree.XMLParser(resolve_entities="internal", no_network=True)
    try:
        root = etree.fromstring(content.data, parser, base_url=content.url)
    except etree.XMLSyntaxError as error:
        raise InvalidManifestError("invalid XML") from error
    if etree.QName(root).localname != "MPD":
        raise InvalidManifestError("invalid MPD")
    # mpd-parser requires lxml elements but annotates the stdlib Element type.
    return MPD(root)  # ty: ignore[invalid-argument-type]


def iter_segment_urls(
    manifest: MPD, base_url: str | None = None, *, now: datetime | None = None
) -> Iterator[str]:
    """Yield initialization and media URLs for every representation in order.

    An override is a directory URL; otherwise the final HTTP URL is used, with
    local references left relative. An empty override disables the HTTP base.
    Live availability uses one snapshot, or a supplied timezone-aware ``now``.
    SegmentError subclasses propagate when advancing the iterator. Keep the
    manifest unchanged during iteration. Byte-range resources retain repeats.
    """
    if base_url:
        base_url = f"{base_url.rstrip('/')}/"
    return manifest.iter_segment_urls(base_url, now=now)


def dumps(manifest: MPD) -> str:
    """Serialize a parsed manifest as XML text."""
    return Parser.to_string(manifest)
