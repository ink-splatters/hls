import sys
from urllib.parse import urljoin

import click
import m3u8

from .. import __version__


class MutuallyExclusiveOption(click.Option):
    """Click option that is mutually exclusive with another option."""

    def __init__(self, *args, not_required_if: list[str] | None = None, **kwargs) -> None:
        self.not_required_if = not_required_if or []
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx: click.Context, opts: dict, args: list) -> tuple:
        current = self.name in opts and opts[self.name] is not None
        for other in self.not_required_if:
            if other in opts and opts[other] is not None and current:
                raise click.UsageError(
                    f"--{self.name.replace('_', '-')} and --{other.replace('_', '-')} are mutually exclusive"
                )
        return super().handle_parse_result(ctx, opts, args)


def source_options(func):
    """Decorator adding -f/--file and -u/--url options."""
    func = click.option(
        "-u",
        "--url",
        type=str,
        default=None,
        help="URL to fetch M3U8 from. Use '-' to read URL from stdin.",
        cls=MutuallyExclusiveOption,
        not_required_if=["file"],
    )(func)
    func = click.option(
        "-f",
        "--file",
        type=click.Path(exists=True, dir_okay=False, allow_dash=True),
        default=None,
        help="File path to read M3U8 from. Use '-' for stdin (default).",
        cls=MutuallyExclusiveOption,
        not_required_if=["url"],
    )(func)
    return func


def load_playlist(file: str | None, url: str | None) -> tuple[m3u8.M3U8, str | None]:
    """Load M3U8 playlist from file or URL.

    Returns:
        Tuple of (playlist, base_url) where base_url is set when loading from URL
    """
    if url is not None:
        # URL mode
        if url == "-":
            # Read URL from stdin
            url = sys.stdin.read().strip()
        return m3u8.load(url), url
    else:
        # File mode (default: stdin)
        if file is None or file == "-":
            content = sys.stdin.read()
            return m3u8.loads(content), None
        else:
            return m3u8.load(file), None


def get_all_urls(playlist: m3u8.M3U8) -> list[str]:
    """Extract all URLs from playlist including init segment."""
    urls: list[str] = []

    # Add init segment if present (from #EXT-X-MAP)
    if playlist.segment_map:
        for init in playlist.segment_map:
            if init.uri:
                urls.append(init.uri)

    # Add all segment URLs
    urls.extend(seg.uri for seg in playlist.segments if seg.uri)

    return urls


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name="hls")
def hls() -> None:
    """HLS playlist utils"""


@hls.command()
@source_options
@click.option("--base-url", type=str, default=None, help="Base URL for resolving relative paths.")
def urls(file: str | None, url: str | None, base_url: str | None) -> None:
    """Extract segment URLs from M3U8 playlist.

    By default reads M3U8 content from stdin. Use -u to fetch from URL.

    Examples:
        cat playlist.m3u8 | hls urls
        hls urls -f playlist.m3u8
        hls urls -u https://example.com/playlist.m3u8
        echo "https://example.com/playlist.m3u8" | hls urls -u -
    """
    playlist, source_url = load_playlist(file, url)

    # Default base_url to source URL if loading from URL
    if base_url is None:
        base_url = source_url

    result = get_all_urls(playlist)

    if base_url:
        result = [urljoin(base_url, u) for u in result]

    print("\n".join(result))


@hls.command()
@source_options
def dump(file: str | None, url: str | None) -> None:
    """Dump M3U8 playlist contents.

    By default reads M3U8 content from stdin. Use -u to fetch from URL.

    Examples:
        cat playlist.m3u8 | hls dump
        hls dump -f playlist.m3u8
        hls dump -u https://example.com/playlist.m3u8
        echo "https://example.com/playlist.m3u8" | hls dump -u -
    """
    playlist, _ = load_playlist(file, url)
    print(playlist.dumps())
