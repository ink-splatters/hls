import pathlib

import click
import pytest

from hls.cli.source import SourceType


@pytest.mark.unit
class TestSourceType:
    """Test SourceType parameter converter."""

    def test_converts_url_to_string(self, mocker):
        """URL inputs should be returned as strings."""
        source_type = SourceType()
        ctx = mocker.Mock(spec=click.Context)
        param = mocker.Mock(spec=click.Parameter)

        result = source_type.convert("https://example.com/playlist.m3u8", param, ctx)

        assert isinstance(result, str)
        assert result == "https://example.com/playlist.m3u8"

    def test_converts_http_url_to_string(self, mocker):
        """HTTP URLs should also be returned as strings."""
        source_type = SourceType()
        ctx = mocker.Mock(spec=click.Context)
        param = mocker.Mock(spec=click.Parameter)

        result = source_type.convert("http://example.com/playlist.m3u8", param, ctx)

        assert isinstance(result, str)
        assert result == "http://example.com/playlist.m3u8"

    def test_converts_existing_file_to_path(self, tmp_path: pathlib.Path, mocker):
        """Existing file paths should be converted to pathlib.Path."""
        test_file = tmp_path / "test.m3u8"
        test_file.write_text("#EXTM3U\n")

        source_type = SourceType()
        ctx = mocker.Mock(spec=click.Context)
        param = mocker.Mock(spec=click.Parameter)

        result = source_type.convert(str(test_file), param, ctx)

        assert isinstance(result, pathlib.Path)
        assert result == test_file

    def test_rejects_nonexistent_file(self):
        """Non-existent file paths should raise BadParameter."""
        source_type = SourceType(path_opts={"exists": True})
        ctx = click.Context(click.Command("test"))
        param = click.Argument(["source"])

        with pytest.raises(click.BadParameter, match="does not exist"):
            source_type.convert("/nonexistent/file.m3u8", param, ctx)

    def test_rejects_directory_by_default(self, tmp_path: pathlib.Path):
        """Directories should be rejected when dir_okay=False (default)."""
        source_type = SourceType(path_opts={"exists": True, "dir_okay": False})
        ctx = click.Context(click.Command("test"))
        param = click.Argument(["source"])

        with pytest.raises(click.BadParameter, match="is a directory"):
            source_type.convert(str(tmp_path), param, ctx)

    def test_accepts_directory_when_allowed(self, tmp_path: pathlib.Path, mocker):
        """Directories should be accepted when dir_okay=True."""
        source_type = SourceType(path_opts={"exists": True, "dir_okay": True})
        ctx = mocker.Mock(spec=click.Context)
        param = mocker.Mock(spec=click.Parameter)

        result = source_type.convert(str(tmp_path), param, ctx)

        assert isinstance(result, pathlib.Path)
        assert result == tmp_path

    def test_custom_path_options(self, tmp_path: pathlib.Path, mocker):
        """Custom path options should be respected."""
        test_file = tmp_path / "test.m3u8"
        test_file.write_text("#EXTM3U\n")

        source_type = SourceType(path_opts={"exists": True, "readable": True})
        ctx = mocker.Mock(spec=click.Context)
        param = mocker.Mock(spec=click.Parameter)

        result = source_type.convert(str(test_file), param, ctx)

        assert isinstance(result, pathlib.Path)
        assert result == test_file

    def test_name_attribute(self):
        """SourceType should have the correct name."""
        source_type = SourceType()
        assert source_type.name == "source"
