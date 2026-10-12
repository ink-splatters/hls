# stream-parser

Python APIs and command-line utilities for HLS (M3U8) playlists and MPEG-DASH
Media Presentation Description (MPD) manifests.
Requires Python 3.14 or newer.

## Installation

```bash
uv tool install --python 3.14 'git+https://github.com/ink-splatters/stream-parser.git'
```

This installs the `hls` and `dash` commands. DASH support uses the
[`mpd-parser` fork](https://github.com/ink-splatters/mpd-parser/tree/v0.3.0-dev)
at `v0.3.0-dev`. PyPI publication is disabled until that dependency is available
from PyPI; install from Git in the meantime.

## Usage

Both commands support `urls` to print segment URLs and `dump` to serialize the
parsed manifest. They read manifest contents from stdin by default.

```bash
hls urls -f playlist.m3u8
dash urls -f manifest.mpd
dash dump -f manifest.mpd
cat manifest.mpd | dash urls
```

Use `-u` to fetch a manifest, and repeat `-H` to supply HTTP headers:

```bash
dash urls -u https://example.com/video/manifest.mpd \
  -H 'Referer: https://example.com/watch' \
  -H 'Authorization: Bearer token'
```

`-u -` reads a URL from stdin; `-f -` reads manifest contents. File and URL
options are mutually exclusive. The same source and header options work with
`hls` and with `dump`.

Both commands accept gzip-compressed HTTP responses. Relative segment URLs
from remote manifests resolve against the fetched URL, including redirects.
For local input, use `--base-url` to supply a directory:

```bash
dash urls -f manifest.mpd --base-url https://cdn.example.com/video/
```

`hls urls` emits initialization URLs followed by media URLs from the loaded
playlist. It does not fetch child playlists referenced by a master playlist.

`dash urls` emits initialization and media URLs for every representation in
manifest order. For live MPDs it emits the currently available segments in one
pass. Neither command polls for updates or downloads media. Resources addressed
by byte ranges retain their repeated URLs; the output does not include ranges.

## Python API

The `stream_parser.hls` and `stream_parser.dash` packages expose `load`,
`iter_segment_urls`, and `dumps` independently of the command-line interfaces:

```python
from pathlib import Path
from stream_parser import dash

manifest = dash.load(Path("manifest.mpd"))
for url in dash.iter_segment_urls(manifest, base_url="https://cdn.example.com/video/"):
    print(url)
```

`load` accepts a filesystem path, HTTP(S) URL, or open binary stream. HTTP headers
can be passed as a mapping with `headers=`. Caller-owned streams remain open.
HLS returns an `m3u8.M3U8`; DASH returns an `mpd_parser` `MPD`.

`iter_segment_urls` returns an iterator. HLS yields initialization URLs followed
by media URLs from the loaded playlist; it does not fetch child playlists.
DASH accepts an optional timezone-aware `now=` for a reproducible live snapshot.
An empty `base_url` disables resolution against the source URL. `dumps` returns
the parsed document as text.

Invalid input raises `stream_parser.hls.InvalidPlaylistError` or
`stream_parser.dash.InvalidManifestError`.
DASH segment errors propagate as `mpd_parser.exceptions.SegmentError` subclasses
during iteration. File and HTTP errors retain their standard exception types.

## Development

```bash
uv sync --locked
uv run poe fix
uv run poe test
```

Tests exercise the protocol APIs and shared input handling; coverage includes
both protocol packages and their CLIs under `stream_parser`.

## TODO

- [x] Load HLS playlists and DASH MPDs from files, stdin, and HTTP(S).
- [x] Serialize parsed manifests and enumerate initialization and media URLs.
- [x] Provide Python APIs and separate `hls` and `dash` commands.
- [ ] Use a PyPI-sourced `mpd-parser` dependency and enable PyPI publication.
- [ ] Download media or delegate to a download manager, with track/representation
      selection and byte-range handling.
- [ ] Assemble downloaded media with FFmpeg, handling initialization segments
      and separate audio/video tracks.
- [ ] Explore a streaming server with configurable segment duration and optional
      media processing.
