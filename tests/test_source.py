"""Transport behavior shared by both protocol packages."""

import gzip
from io import BytesIO
from typing import TYPE_CHECKING
from urllib.error import HTTPError

import pytest

from stream_parser.common.source import read_source

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("as_string", [False, True])
def test_file_bytes_have_no_remote_base(data_dir: Path, as_string: bool) -> None:
    path = data_dir / "dash" / "latin1.mpd"

    content = read_source(str(path) if as_string else path)

    assert content.data == path.read_bytes()
    assert content.url is None


def test_caller_owned_stream_is_read_from_current_position_and_left_open() -> None:
    with BytesIO(b"prefix<MPD/>") as stream:
        stream.seek(6)

        content = read_source(stream)

        assert content.data == b"<MPD/>"
        assert content.url is None
        assert not stream.closed


def test_missing_file_retains_os_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.mpd"

    with pytest.raises(FileNotFoundError) as caught:
        read_source(path)

    assert caught.value.filename == str(path)


@pytest.mark.integration
def test_redirect_retains_final_url_and_request_headers(manifest_server, data_dir: Path) -> None:
    base_url, requests = manifest_server
    headers = {"Referer": "https://example.com/watch", "Authorization": "Bearer test-token"}

    content = read_source(f"{base_url}/redirect/dash/manifest.mpd", headers=headers)

    assert content.url == f"{base_url}/dash/manifest.mpd"
    assert content.data == (data_dir / "dash" / "manifest.mpd").read_bytes()
    assert len(requests) == 2
    for request in requests:
        assert request["Referer"] == headers["Referer"]
        assert request["Authorization"] == headers["Authorization"]


@pytest.mark.integration
def test_gzip_response_retains_bytes_and_location(manifest_server, data_dir: Path) -> None:
    base_url, _ = manifest_server
    url = f"{base_url}/gzip/dash/latin1.mpd"

    content = read_source(url)

    assert content.data == (data_dir / "dash" / "latin1.mpd").read_bytes()
    assert content.url == url


@pytest.mark.integration
def test_http_failure_retains_status_and_url(manifest_server) -> None:
    base_url, _ = manifest_server
    url = f"{base_url}/missing.mpd"

    with pytest.raises(HTTPError) as caught:
        read_source(url)

    assert caught.value.code == 404
    assert caught.value.url == url
    caught.value.close()


@pytest.mark.integration
def test_invalid_gzip_is_not_passed_to_a_protocol_parser(manifest_server) -> None:
    base_url, _ = manifest_server

    with pytest.raises(gzip.BadGzipFile):
        read_source(f"{base_url}/broken-gzip")
