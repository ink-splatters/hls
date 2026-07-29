import m3u8
import pytest
from click.testing import CliRunner

from hls.cli import hls, infer_base_url, load_playlist

PLAYLIST = "#EXTM3U\n#EXTINF:1,\nsegment.ts\n"
MEDIA_PLAYLIST_URL = (
    "https://hv-h.phncdn.com/hls/c6251/videos/202512/29/34178225/"
    "1080P_4000K_34178225.mp4/index-v1-a1.m3u8?h=token"
)
MEDIA_BASE_URL = (
    "https://hv-h.phncdn.com/hls/c6251/videos/202512/29/34178225/1080P_4000K_34178225.mp4"
)


@pytest.mark.unit
class TestBaseUrlInference:
    def test_infers_file_like_parent_from_m3u8_base_uri(self):
        playlist = m3u8.loads(PLAYLIST, uri=MEDIA_PLAYLIST_URL)

        assert infer_base_url(playlist) == MEDIA_BASE_URL

    def test_does_not_infer_directory_without_file_extension(self):
        playlist = m3u8.loads(PLAYLIST, uri="https://example.com/hls/index.m3u8")

        assert infer_base_url(playlist) is None

    def test_urls_uses_inferred_base_url(self, mocker):
        playlist = m3u8.loads(PLAYLIST, uri=MEDIA_PLAYLIST_URL)
        mocker.patch("hls.cli.m3u8.load", return_value=playlist)

        result = CliRunner().invoke(hls, ["urls", "--url", MEDIA_PLAYLIST_URL])

        assert result.exit_code == 0
        assert result.output == f"{MEDIA_BASE_URL}/segment.ts\n"

    def test_urls_leaves_relative_urls_when_inference_fails(self, mocker):
        playlist_url = "https://example.com/hls/index.m3u8"
        playlist = m3u8.loads(PLAYLIST, uri=playlist_url)
        mocker.patch("hls.cli.m3u8.load", return_value=playlist)

        result = CliRunner().invoke(hls, ["urls", "--url", playlist_url])

        assert result.exit_code == 0
        assert result.output == "segment.ts\n"

    def test_explicit_base_url_skips_inference(self, mocker):
        playlist = m3u8.loads(PLAYLIST, uri=MEDIA_PLAYLIST_URL)
        mocker.patch("hls.cli.m3u8.load", return_value=playlist)
        infer = mocker.patch("hls.cli.infer_base_url")

        result = CliRunner().invoke(
            hls,
            ["urls", "--url", MEDIA_PLAYLIST_URL, "--base-url", "https://cdn.example/media"],
        )

        assert result.exit_code == 0
        assert result.output == "https://cdn.example/media/segment.ts\n"
        infer.assert_not_called()


@pytest.mark.unit
class TestRequestHeaders:
    def test_load_playlist_passes_multiple_headers_to_m3u8(self, mocker):
        load = mocker.patch("hls.cli.m3u8.load", return_value=m3u8.loads(PLAYLIST))

        load_playlist(
            None,
            MEDIA_PLAYLIST_URL,
            (("Referer", "https://example.com/watch"), ("User-Agent", "hls-test")),
        )

        load.assert_called_once_with(
            MEDIA_PLAYLIST_URL,
            headers={"Referer": "https://example.com/watch", "User-Agent": "hls-test"},
        )

    @pytest.mark.parametrize("command", ["urls", "dump"])
    def test_download_aware_commands_accept_repeated_headers(self, command, mocker):
        load = mocker.patch(
            "hls.cli.m3u8.load",
            return_value=m3u8.loads(PLAYLIST, uri=MEDIA_PLAYLIST_URL),
        )

        result = CliRunner().invoke(
            hls,
            [
                command,
                "--url",
                MEDIA_PLAYLIST_URL,
                "-H",
                "Referer: https://example.com/watch",
                "--headers",
                "Authorization: Bearer secret",
            ],
        )

        assert result.exit_code == 0
        load.assert_called_once_with(
            MEDIA_PLAYLIST_URL,
            headers={
                "Referer": "https://example.com/watch",
                "Authorization": "Bearer secret",
            },
        )

    def test_rejects_malformed_header(self):
        result = CliRunner().invoke(
            hls,
            ["urls", "--url", MEDIA_PLAYLIST_URL, "-H", "Authorization"],
        )

        assert result.exit_code == 2
        assert "must be in 'Name: value' form" in result.output
