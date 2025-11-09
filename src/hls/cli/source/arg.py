import functools as f
import typing as t
from collections.abc import Callable

import click

from .type import SourceType


def source_arg(
    wrapped: Callable[..., t.Any] | None = None,
    *,
    path_opts: dict[str, t.Any] | None = None,
    url_opts: dict[str, t.Any] | None = None,
    name: str = "source",
) -> Callable[..., t.Any]:
    """Decorator to add a source argument with default options.

    Can be used with or without parentheses:
        @source_arg
        @source_arg()
        @source_arg(path_opts={"exists": True})
    """
    # Set defaults
    if path_opts is None:
        path_opts = {"exists": True, "dir_okay": False}

    # This is the actual decorator that will be applied
    def decorator(func: Callable[..., t.Any]) -> Callable[..., t.Any]:
        return click.argument(
            name,
            type=SourceType(path_opts=path_opts, url_opts=url_opts)
        )(func)

    # If called with a function directly (without parens), apply immediately
    if wrapped is not None:
        return decorator(wrapped)

    # Otherwise return the decorator to be applied
    return decorator
