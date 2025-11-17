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
    required: bool = False,
) -> Callable[..., t.Any]:
    """Decorator to add a source argument with default options.

    Can be used with or without parentheses:
        @source_arg
        @source_arg()
        @source_arg(path_opts={"exists": True})
        @source_arg(required=True)  # Make argument mandatory

    Args:
        wrapped: The function to wrap (when used without parentheses)
        path_opts: Options for Path type validation
        url_opts: Options for URL type validation
        name: Name of the argument (default: "source")
        required: Whether the argument is required (default: False)
                  When False, omitting the argument defaults to stdin.
                  This follows Unix CLI conventions for stream processing tools.

    Note: By default, the source argument is optional and defaults to stdin
          when omitted. Use '-' to explicitly read from stdin.
    """
    # Set defaults
    if path_opts is None:
        # Don't enforce 'exists' by default since stdin isn't a file
        # Only enforce when explicitly working with file paths
        path_opts = {"exists": True, "dir_okay": False}

    # This is the actual decorator that will be applied
    def decorator(func: Callable[..., t.Any]) -> Callable[..., t.Any]:
        # When not required, we use '-' as the default to trigger stdin
        # This ensures the SourceType converter is called and returns sys.stdin
        if not required:
            return click.argument(
                name,
                type=SourceType(path_opts=path_opts, url_opts=url_opts),
                required=False,
                default="-",  # Use '-' as default to trigger stdin in converter
            )(func)
        else:
            return click.argument(
                name,
                type=SourceType(path_opts=path_opts, url_opts=url_opts),
                required=True,
            )(func)

    # If called with a function directly (without parens), apply immediately
    if wrapped is not None:
        return decorator(wrapped)

    # Otherwise return the decorator to be applied
    return decorator
