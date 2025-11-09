import inspect
import pathlib

import click
import pytest

from hls.cli.source import Source, source_arg


@pytest.mark.unit
class TestSourceArgDecorator:
    """Test source_arg decorator."""

    def test_decorator_without_parentheses(self):
        """source_arg can be used without parentheses."""
        @source_arg
        def my_command(source: Source) -> None:
            pass

        # Check that the decorator was applied
        assert hasattr(my_command, "__click_params__")
        params = my_command.__click_params__  # type: ignore[attr-defined]
        assert len(params) == 1
        assert params[0].name == "source"

    def test_decorator_with_parentheses(self):
        """source_arg can be used with parentheses."""
        @source_arg()
        def my_command(source: Source) -> None:
            pass

        # Check that the decorator was applied
        assert hasattr(my_command, "__click_params__")
        params = my_command.__click_params__  # type: ignore[attr-defined]
        assert len(params) == 1
        assert params[0].name == "source"

    def test_decorator_with_custom_name(self):
        """source_arg accepts custom argument name."""
        @source_arg(name="playlist")
        def my_command(playlist: Source) -> None:
            pass

        params = my_command.__click_params__  # type: ignore[attr-defined]
        assert params[0].name == "playlist"

    def test_decorator_with_custom_path_opts(self):
        """source_arg accepts custom path options."""
        @source_arg(path_opts={"exists": True, "dir_okay": True})
        def my_command(source: Source) -> None:
            pass

        params = my_command.__click_params__  # type: ignore[attr-defined]
        assert params[0].name == "source"
        # The type should be SourceType
        assert params[0].type.__class__.__name__ == "SourceType"

    def test_decorator_preserves_function_name(self):
        """source_arg preserves the original function name."""
        @source_arg
        def my_command(source: Source) -> None:
            pass

        assert my_command.__name__ == "my_command"

    def test_decorator_preserves_docstring(self):
        """source_arg preserves the original function docstring."""
        @source_arg
        def my_command(source: Source) -> None:
            """This is my command."""
            pass

        assert my_command.__doc__ == "This is my command."

    def test_decorator_preserves_signature(self):
        """source_arg preserves the original function signature for introspection."""
        def original_function(source: Source, verbose: bool = False) -> None:
            """Original function."""
            pass

        @source_arg
        def decorated_function(source: Source, verbose: bool = False) -> None:
            """Decorated function."""
            pass

        # Get signatures
        original_sig = inspect.signature(original_function)
        decorated_sig = inspect.signature(decorated_function)

        # Compare parameters (click adds some internal stuff, but base signature should match)
        original_params = list(original_sig.parameters.keys())
        decorated_params = list(decorated_sig.parameters.keys())

        assert original_params == decorated_params
        assert str(original_sig) == str(decorated_sig)

    def test_decorator_can_stack_with_other_decorators(self):
        """source_arg can be stacked with other Click decorators."""
        @click.option("--verbose", is_flag=True)
        @source_arg
        def my_command(source: Source, verbose: bool) -> None:
            pass

        params = my_command.__click_params__  # type: ignore[attr-defined]  # type: ignore[attr-defined]
        assert len(params) == 2
        # Check both params exist (order may vary)
        param_names = {p.name for p in params}
        assert param_names == {"verbose", "source"}

    def test_decorator_uses_default_path_opts(self):
        """source_arg uses default path options when not specified."""
        @source_arg()
        def my_command(source: Source) -> None:
            pass

        params = my_command.__click_params__  # type: ignore[attr-defined]
        source_param = params[0]

        # The SourceType should have been created with default options
        assert source_param.type._path_opts["exists"] is True
        assert source_param.type._path_opts["dir_okay"] is False

    def test_decorated_function_is_callable(self):
        """Decorated function remains callable."""
        @source_arg
        def my_command(source: Source) -> str:
            return f"Got source: {source}"

        # The function should still be callable
        assert callable(my_command)

    def test_multiple_decorations_with_different_names(self):
        """Can use source_arg multiple times with different names (edge case)."""
        @source_arg(name="output")
        @source_arg(name="input")
        def my_command(input: Source, output: Source) -> None:
            pass

        params = my_command.__click_params__  # type: ignore[attr-defined]
        assert len(params) == 2
        # Check both params exist (order may vary)
        param_names = {p.name for p in params}
        assert param_names == {"output", "input"}

    def test_signature_with_type_annotations(self):
        """Decorator preserves type annotations."""
        @source_arg
        def my_command(source: Source, count: int = 5) -> list[str]:
            return []

        sig = inspect.signature(my_command)
        params = sig.parameters

        assert "source" in params
        assert "count" in params
        assert params["source"].annotation == Source
        assert params["count"].annotation == int
        assert sig.return_annotation == list[str]
