import inspect
from argparse import ArgumentParser
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Tuple, Type, Union

from pydantic import BaseModel
from typing_extensions import ContextManager

from pydantic_argparse_builder.parse import build_parser

_registry: Dict[Union[str, None], Tuple[Callable[[BaseModel], None]]] = {}


def get_command_model(func: Callable[[BaseModel], None]) -> Type[BaseModel]:
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
    return spec.annotations[spec.args[0]]


def main():
    """Start application"""
    # Build parser
    parser = ArgumentParser()
    if len(_registry) == 1 and None in _registry:
        build_parser(parser, get_command_model(_registry[None]))
        parser.set_defaults(_command=None)
    else:
        subparsers = parser.add_subparsers(dest="_command")
        for command, callback in _registry.items():
            subparser = subparsers.add_parser(command)
            build_parser(subparser, get_command_model(callback))
    args = parser.parse_args()

    if args._command not in _registry:
        parser.print_help()
        return

    # Start application
    kwargs = vars(args)
    callback = _registry[args._command]
    del kwargs["_command"]
    callback(get_command_model(callback)(**kwargs))


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
            print("Before building argument parsers!")
            try:
                yield
            except Exception as e:
                print("Error hamdling!", e)
            finally:
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

        from pydantic_argparse_builder import command, main
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
        raise ValueError("Only one command is allowed.")
    _registry[None] = func
    return func


def sub_command(name: str):
    """Decorator for sub command"""

    def _(func: Any):
        if name in _registry:
            raise ValueError("Command name is already used.")
        _registry[name] = func
        return func

    return _
