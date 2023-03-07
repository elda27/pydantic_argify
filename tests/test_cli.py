import sys
from copy import deepcopy

import pytest
from pydantic import BaseModel

from pydantic_argparse_builder import command, entrypoint, main, sub_command
from pydantic_argparse_builder.cli import get_command_model


@pytest.fixture
def registry():
    from pydantic_argparse_builder.cli import _registry

    _registry.clear()
    yield
    _registry.clear()


def test_get_command_model():
    class Config(BaseModel):
        name: str
        age: int
        is_active: bool

    def launch(config: Config):
        print(config)

    assert get_command_model(launch) is Config


def test_cli_command(registry):
    class Config(BaseModel):
        name: str
        age: int
        is_active: bool

    @command
    def launch(config: Config):
        print(config)

    from pydantic_argparse_builder.cli import _registry

    assert len(_registry) == 1
    assert None in _registry
    assert _registry[None] is launch

    with pytest.raises(ValueError):

        @command
        def launch3(config: Config):
            print(config)


def test_cli_sub_command(registry):
    class Config1(BaseModel):
        name: str
        age: int
        is_active: bool

    @sub_command("launch1")
    def launch1(config: Config1):
        print(config)

    class Config2(BaseModel):
        name: str
        age: int
        is_active: bool

    @sub_command("launch2")
    def launch2(config: Config2):
        print(config)

    from pydantic_argparse_builder.cli import _registry

    assert len(_registry) == 2
    assert "launch1" in _registry
    assert _registry["launch1"] is launch1
    assert "launch2" in _registry
    assert _registry["launch2"] is launch2

    with pytest.raises(ValueError):

        @sub_command("launch1")
        def launch3(config: Config1):
            print(config)


def test_entrypoint(registry):
    class Config(BaseModel):
        name: str = None
        age: int = None
        is_active: bool = None

    count = 0

    @command
    def launch(config: Config):
        assert count == 1

    @entrypoint
    def main():
        nonlocal count
        count += 1
        yield
        count += 1

    try:
        argv = deepcopy(sys.argv)
        sys.argv = ["main"]
        main()
    finally:
        sys.argv = argv
    assert count == 2


def test_main_with_command(registry):
    class Config(BaseModel):
        name: str = None
        age: int = None
        is_active: bool = None

    count = 0

    @command
    def launch(config: Config):
        nonlocal count
        count += 1

    assert count == 0
    try:
        argv = deepcopy(sys.argv)
        sys.argv = ["main"]
        main()
    finally:
        sys.argv = argv
    assert count == 1


def test_main_with_sub_command(registry):
    count = 0

    class Config1(BaseModel):
        name: str = None
        age: int = None
        is_active: bool = None

    @sub_command("launch1")
    def launch1(config: Config1):
        nonlocal count
        count += 1

    class Config2(BaseModel):
        name: str = None
        age: int = None
        is_active: bool = None

    @sub_command("launch2")
    def launch2(config: Config2):
        nonlocal count
        count += 2

    assert count == 0
    try:
        argv = deepcopy(sys.argv)
        sys.argv = ["main"]
        main()
    finally:
        sys.argv = argv
    assert count == 0

    # launch1
    try:
        argv = deepcopy(sys.argv)
        sys.argv = ["main", "launch1"]
        main()
    finally:
        sys.argv = argv
    assert count == 1

    # launch2
    try:
        argv = deepcopy(sys.argv)
        sys.argv = ["main", "launch2"]
        main()
    finally:
        sys.argv = argv
    assert count == 3
