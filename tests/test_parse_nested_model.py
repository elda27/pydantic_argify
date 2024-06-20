from argparse import ArgumentParser

from pydantic import BaseModel, Field

from pydantic_argify import build_parser


def test_nested_model():
    class ChildConfig(BaseModel):
        name: str
        age: int = Field(10)
        is_active: bool

    class Config(BaseModel):
        name: str
        child: ChildConfig

    parser = ArgumentParser()
    build_parser(parser, Config)

    a = parser._actions
    # Config.name
    assert "--name" in a[1].option_strings
    assert "name" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].help is None
    # Config.name
    assert "--child.name" in a[2].option_strings
    assert a[2].type is str
    assert a[2].default is None
    assert a[2].required
    assert a[2].help is None
    # Config.age
    assert "--child.age" in a[3].option_strings
    assert a[3].type is int
    assert a[3].default == 10
    assert not a[3].required
    assert a[3].help is None
    # Config.is_active
    assert "--child.is-active" in a[4].option_strings
    assert a[4].type is bool
    assert a[4].default is None
    assert a[4].required
    assert a[4].help is None

    args = parser.parse_args(
        [
            "--name",
            "test",
            "--child.name",
            "child_test",
            "--child.age",
            "10",
            "--child.is-active",
            "true",
        ]
    )
    assert Config(
        **{
            "name": "test",
            "child": {"name": "child_test", "age": 10, "is_active": True},
        }
    ) == Config.model_validate(vars(args))
