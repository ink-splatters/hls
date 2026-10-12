"""DASH loading and integration with the dependency's segment model."""

from datetime import UTC, datetime
from io import BytesIO
from typing import TYPE_CHECKING

import pytest
from lxml import etree
from mpd_parser.exceptions import SegmentError

from stream_parser import dash

if TYPE_CHECKING:
    from pathlib import Path


def test_local_manifest_emits_initialization_and_media_urls(data_dir: Path) -> None:
    manifest = dash.load(data_dir / "dash" / "manifest.mpd")

    assert list(dash.iter_segment_urls(manifest)) == [
        "init.mp4",
        "chunk-1.m4s",
        "chunk-2.m4s",
        "chunk-3.m4s",
    ]


@pytest.mark.parametrize("base_url", ["https://cdn.example/video", "https://cdn.example/video/"])
def test_base_override_is_a_directory(data_dir: Path, base_url: str) -> None:
    manifest = dash.load(data_dir / "dash" / "manifest.mpd")

    assert next(dash.iter_segment_urls(manifest, base_url)) == "https://cdn.example/video/init.mp4"


@pytest.mark.integration
def test_remote_manifest_uses_redirect_directory(manifest_server) -> None:
    base_url, _ = manifest_server
    manifest = dash.load(f"{base_url}/redirect/dash/manifest.mpd")

    assert next(dash.iter_segment_urls(manifest)) == f"{base_url}/dash/init.mp4"


@pytest.mark.integration
def test_remote_base_can_be_replaced_or_disabled(manifest_server) -> None:
    base_url, _ = manifest_server
    manifest = dash.load(f"{base_url}/dash/manifest.mpd")

    assert next(dash.iter_segment_urls(manifest, "https://cdn.example/video")) == (
        "https://cdn.example/video/init.mp4"
    )
    assert next(dash.iter_segment_urls(manifest, "")) == "init.mp4"


def test_file_honors_xml_encoding_declaration(data_dir: Path) -> None:
    manifest = dash.load(data_dir / "dash" / "latin1.mpd")

    assert manifest.id == "café"


def test_binary_stream_honors_xml_encoding_declaration(data_dir: Path) -> None:
    with BytesIO((data_dir / "dash" / "latin1.mpd").read_bytes()) as stream:
        manifest = dash.load(stream)

    assert manifest.id == "café"


def test_serialization_preserves_segment_description(data_dir: Path) -> None:
    manifest = dash.load(data_dir / "dash" / "manifest.mpd")

    restored = dash.load(BytesIO(dash.dumps(manifest).encode("utf-8")))

    assert list(dash.iter_segment_urls(restored)) == list(dash.iter_segment_urls(manifest))


def test_malformed_xml_retains_parser_cause() -> None:
    with pytest.raises(dash.InvalidManifestError, match="invalid XML") as caught:
        dash.load(BytesIO(b"<MPD>"))

    assert isinstance(caught.value.__cause__, etree.XMLSyntaxError)


def test_non_mpd_document_is_rejected() -> None:
    with pytest.raises(dash.InvalidManifestError, match="invalid MPD"):
        dash.load(BytesIO(b"<html/>"))


def test_segment_errors_are_deferred_until_iteration(data_dir: Path) -> None:
    manifest = dash.load(data_dir / "dash" / "invalid-timing.mpd")

    urls = dash.iter_segment_urls(manifest)

    with pytest.raises(SegmentError):
        next(urls)


def test_live_snapshot_uses_supplied_time(data_dir: Path) -> None:
    manifest = dash.load(data_dir / "dash" / "live.mpd")
    now = datetime(2026, 1, 1, 0, 0, 10, tzinfo=UTC)

    assert list(dash.iter_segment_urls(manifest, now=now)) == [
        "init.mp4",
        "chunk-4.m4s",
        "chunk-5.m4s",
    ]
