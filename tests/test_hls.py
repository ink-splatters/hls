"""HLS loading, serialization, and segment URL behavior through the public API."""

from io import BytesIO
from typing import TYPE_CHECKING

import pytest

from stream_parser import hls

if TYPE_CHECKING:
    from pathlib import Path


def test_local_playlist_emits_initialization_then_media_urls(data_dir: Path) -> None:
    playlist = hls.load(data_dir / "hls" / "media.m3u8")

    assert list(hls.iter_segment_urls(playlist)) == [
        "init.mp4",
        "part-1.m4s",
        "/shared/part-2.m4s",
        "https://other.example/part-3.m4s",
    ]


@pytest.mark.parametrize("base_url", ["https://cdn.example/video", "https://cdn.example/video/"])
def test_base_override_resolves_relative_and_preserves_absolute_urls(
    data_dir: Path, base_url: str
) -> None:
    playlist = hls.load(data_dir / "hls" / "media.m3u8")

    assert list(hls.iter_segment_urls(playlist, base_url)) == [
        "https://cdn.example/video/init.mp4",
        "https://cdn.example/video/part-1.m4s",
        "https://cdn.example/shared/part-2.m4s",
        "https://other.example/part-3.m4s",
    ]


@pytest.mark.integration
def test_remote_playlist_uses_redirect_directory(manifest_server) -> None:
    base_url, _ = manifest_server
    playlist = hls.load(f"{base_url}/redirect/hls/media.m3u8?token=test")

    assert next(hls.iter_segment_urls(playlist)) == f"{base_url}/hls/init.mp4"


@pytest.mark.integration
def test_remote_base_can_be_replaced_or_disabled(manifest_server) -> None:
    base_url, _ = manifest_server
    playlist = hls.load(f"{base_url}/hls/media.m3u8")

    assert next(hls.iter_segment_urls(playlist, "https://cdn.example/video")) == (
        "https://cdn.example/video/init.mp4"
    )
    assert next(hls.iter_segment_urls(playlist, "")) == "init.mp4"


def test_byte_ranges_keep_repeated_resource_urls(data_dir: Path) -> None:
    playlist = hls.load(data_dir / "hls" / "byte-ranges.m3u8")

    assert list(hls.iter_segment_urls(playlist)) == ["media.ts", "media.ts"]


def test_master_playlist_does_not_fetch_child_playlists(data_dir: Path) -> None:
    playlist = hls.load(data_dir / "hls" / "master.m3u8")

    assert list(hls.iter_segment_urls(playlist)) == []


def test_serialization_preserves_playlist_content(data_dir: Path) -> None:
    playlist = hls.load(data_dir / "hls" / "media.m3u8")

    restored = hls.load(BytesIO(hls.dumps(playlist).encode("utf-8")))

    assert list(hls.iter_segment_urls(restored)) == list(hls.iter_segment_urls(playlist))
    assert restored.segments[0].title == "café"
    assert restored.data["targetduration"] == 4
    assert restored.data["is_endlist"]


def test_non_utf8_input_raises_playlist_error() -> None:
    with pytest.raises(hls.InvalidPlaylistError, match="invalid UTF-8") as caught:
        hls.load(BytesIO(b"#EXTM3U\n#\xff\n"))

    assert isinstance(caught.value.__cause__, UnicodeDecodeError)


def test_non_playlist_input_is_rejected() -> None:
    with pytest.raises(hls.InvalidPlaylistError, match="missing #EXTM3U header"):
        hls.load(BytesIO(b"<html/>"))


def test_invalid_tag_value_raises_playlist_error() -> None:
    with pytest.raises(hls.InvalidPlaylistError, match="invalid playlist") as caught:
        hls.load(BytesIO(b"#EXTM3U\n#EXT-X-TARGETDURATION:invalid\n"))

    assert isinstance(caught.value.__cause__, ValueError)
