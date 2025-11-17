import io
from urllib.parse import urljoin

import click
import m3u8
from click_params import PUBLIC_URL

from .. import __version__
from .source import Source, source_arg  # SourceType,


def load_playlist(source: Source) -> m3u8.M3U8:
    """Load M3U8 playlist from various source types.

    Args:
        source: Can be a Path (file), str (URL), or TextIOWrapper (stdin)

    Returns:
        Loaded M3U8 playlist object
    """
    if isinstance(source, io.TextIOWrapper):
        # Read from stdin or any file object
        content = source.read()
        return m3u8.loads(content)
    else:
        # Path or URL - m3u8.load handles both
        return m3u8.load(str(source))


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name="hls")
def hls() -> None:
    """HLS playlist utils"""


@hls.command()
@source_arg()
@click.option("--base-url", type=PUBLIC_URL)
def urls(source: Source, base_url: str | None) -> None:
    """Produces a list of URLs from m3u8 SOURCE.

    SOURCE can be a URL, file path, or '-' for stdin. If omitted, reads from stdin.

    When SOURCE is a URL, --base-url defaults to that URL for resolving relative segment paths.

    Examples:
        hls urls playlist.m3u8
        hls urls https://example.com/playlist.m3u8
        hls urls -  # Read from stdin
        hls urls    # Read from stdin (default)
        cat playlist.m3u8 | hls urls
        curl -s https://example.com/playlist.m3u8 | hls urls
    """

    playlist = load_playlist(source)

    # Default base_url to source URL if source is a URL (not stdin or file)
    if base_url is None and isinstance(source, str):
        base_url = source

    urls: list[str] = [seg.uri for seg in playlist.segments if seg.uri]

    if base_url:
        urls = [urljoin(base_url, url) for url in urls]

    print("\n".join(urls))


@hls.command()
@source_arg()
def dump(source: Source) -> None:
    """Dumps contents of m3u8 playlist from SOURCE.

    SOURCE can be a URL, file path, or '-' for stdin. If omitted, reads from stdin.

    Examples:
        hls dump playlist.m3u8
        hls dump https://example.com/playlist.m3u8
        hls dump -  # Read from stdin
        hls dump    # Read from stdin (default)
        cat playlist.m3u8 | hls dump
        curl -s https://example.com/playlist.m3u8 | hls dump
    """

    playlist = load_playlist(source)

    print(playlist.dumps())
