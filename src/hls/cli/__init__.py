import functools as f
from urllib.parse import urljoin

import click
import m3u8
from click_params import PUBLIC_URL

from .. import __version__
from .source import Source, source_arg  # SourceType,


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name="hls")
def hls() -> None:
    """HLS playlist utils"""


@hls.command()
@source_arg()
@click.option("--base-url", type=PUBLIC_URL)
def urls(source: Source, base_url: str | None) -> None:
    """Produces a list of URLs from m3u8 SOURCE.

    SOURCE can be URL or file path.

    When SOURCE is a URL, --base-url defaults to that URL for resolving relative segment paths.
    """

    playlist = m3u8.load(str(source))

    # Default base_url to source URL if source is a URL
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

    SOURCE can be URL or Path.
    """

    playlist = m3u8.load(str(source))

    print(playlist.dumps())
