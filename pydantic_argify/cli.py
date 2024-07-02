import inspect
import typing
from argparse import ArgumentParser
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, List, Tuple, Type, Union, overload

from pydantic import BaseModel
from typing_extensions import ContextManager

from pydantic_argify.parse import build_parser

_registry: Dict[Union[str, None], Tuple[Callable[[BaseModel], None]]] = {}


def get_command_model(func: Callable[[BaseModel], None]) -> Type[BaseModel] | None:
    """Get model from command function

    Parameters
    ----------
    func : Callable[[BaseModel], None]
        callable object

    Returns
    -------
    Type[BaseModel]
        parsed type
    """
    spec = inspect.getfullargspec(func)
    if len(spec.args) == 0:
        # No argument
        return None
    else:
        return spec.annotations[spec.args[0]]


if typing.TYPE_CHECKING:

    @overload
    def main(
        excludes: List[str] = [],
        auto_truncate: bool = True,
        groupby_inherit: bool = True,
        exclude_truncated_args: list[str] = ["-h"],
        parse_nested_model: bool = True,
        naming_separator: str = "-",
    ): ...

    @overload
    def main(**kwargs): ...


def main(**kwargs):
    """Start application"""
    # Build parser
    parser = ArgumentParser()
    if len(_registry) == 1 and None in _registry:
        build_parser(parser, get_command_model(_registry[None]), **kwargs)
        parser.set_defaults(_command=None)
    else:
        subparsers = parser.add_subparsers(dest="_command")
        for command, callback in _registry.items():
            subparser = subparsers.add_parser(command)
            build_parser(subparser, get_command_model(callback), **kwargs)
    args = parser.parse_args()

    if args._command not in _registry:
        parser.print_help()
        return

    # Start application
    kwargs = vars(args)
    callback = _registry[args._command]
    del kwargs["_command"]

    model_type = get_command_model(callback)
    if model_type is not None:
        callback(model_type(**kwargs))
    else:
        callback()


def entrypoint(func: Any) -> ContextManager[None]:
    """Decorator for entrypoint of application

    Parameters
    ----------
    func : Any
        Function to be decorated

    Example
    -------
        @entrypoint
        def main():
            # You can initialization such as logging, etc.
            print("Before building argument parsers!")
            try:
                yield
            except Exception as e:
                # You can handle exceptions here
                print("Error hamdling!", e)
            finally:
                # You can something finalization here
                print("End!")

    """
    _func = contextmanager(func)

    @wraps(func)
    def _():
        with _func():
            main()

    return _


def command(func: Any):
    """Command decorator for application
    You can create an application similar to `click`.

    Note: This decorator can be used only once.

    Example
    -------
    example.py

        from pydantic_argify import command, main
        class Config(BaseModel):
            string: str = Field(description="string parameter")
            integer: int = Field(description="integer parameter")
        @command
        def command(config: Config):
            print(config)
        main()

        $> python example.py --string "Hello" --integer 1
        string='Hello', integer=1
    """
    if len(_registry) > 0:
        if None in _registry and _registry[None] is func:
            return func  # Already registered
        raise ValueError("Only one command is allowed.")
    _registry[None] = func
    return func


def sub_command(name: str):
    """Decorator for sub command"""

    def _(func: Any):
        if name in _registry:
            if _registry[name] is func:
                return func  # Already registered
            raise ValueError("Command name is already used.")
        _registry[name] = func
        return func

    return _
