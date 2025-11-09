import pathlib
import typing as t
from urllib.parse import urlparse

import click

# https://click-params.readthedocs.io
from click_params.domain import UrlParamType

from .source import Source


class SourceType(click.ParamType):
    """Click parameter type for Source: URL or filesystem path."""

    name = "source"

    def __init__(
        self, *, path_opts: dict[str, t.Any] | None = None, url_opts: dict[str, t.Any] | None = None
    ) -> None:
        path_opts = path_opts if path_opts else {}
        if "path_type" not in path_opts:
            path_opts |= {"path_type": pathlib.Path}

        self._path_opts = path_opts

        url_opts = url_opts if url_opts else {}
        if "may_have_port" not in url_opts:
            url_opts |= {"may_have_port": True}

        self._url_opts = url_opts

    def convert(
        self,
        value: str,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Source:
        """Source converter
        Returns string if urlparse detected schema, otherwise Path (pathlib.Path by default).
        """

        if urlparse(value).scheme:
            param_type = UrlParamType(**self._url_opts)
            return t.cast(str, param_type.convert(value, param, ctx))
        else:
            param_type = click.Path(**self._path_opts)
            return t.cast(pathlib.Path, param_type.convert(value, param, ctx))
