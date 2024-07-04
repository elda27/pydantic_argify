from argparse import ArgumentParser

from pydantic import BaseModel, Field, SecretStr

from pydantic_argify import build_parser


def test_nested_model():
    class ChildConfig(BaseModel):
        name: str
        age: int = Field(10)
        is_active: bool

    class ChildConfig2(BaseModel):
        name: str
        age: int = Field(10)
        is_active: bool

    class Config(BaseModel):
        name: str
        child: ChildConfig
        child2: ChildConfig2 | None = Field(None)

    parser = ArgumentParser()
    build_parser(parser, Config)

    a = parser._actions
    # name
    assert "--name" in a[1].option_strings
    assert "name" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].help is None
    # child.name
    assert "--child.name" in a[2].option_strings
    assert a[2].type is str
    assert a[2].default is None
    assert a[2].required
    assert a[2].help is None
    # child.age
    assert "--child.age" in a[3].option_strings
    assert a[3].type is int
    assert a[3].default == 10
    assert not a[3].required
    assert a[3].help is None
    # child.is_active
    assert "--child.is-active" in a[4].option_strings
    assert a[4].type is bool
    assert a[4].default is None
    assert a[4].required
    assert a[4].help is None
    # child2.name
    assert "--child2.name" in a[5].option_strings
    assert a[5].type is str
    assert a[5].default is None
    assert not a[5].required
    assert a[5].help is None
    # child2.age
    assert "--child2.age" in a[6].option_strings
    assert a[6].type is int
    assert a[6].default == 10
    assert not a[6].required
    assert a[6].help is None
    # child2.is_active
    assert "--child2.is-active" in a[7].option_strings
    assert a[7].type is bool
    assert a[7].default is None
    assert not a[7].required
    assert a[7].help is None
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


def test_nested_model_with_naming_separator():
    class ChildConfig(BaseModel):
        name: str
        age: int = Field(10)
        is_active: bool

    class ChildConfig2(BaseModel):
        name: str
        age: int = Field(10)
        is_active: bool

    class Config(BaseModel):
        name: str
        child: ChildConfig
        child2: ChildConfig2 | None = Field(None)

    parser = ArgumentParser()
    build_parser(parser, Config, naming_separator="_")

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
    assert "--child.is_active" in a[4].option_strings
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
            "--child.is_active",
            "true",
        ]
    )
    assert Config(
        **{
            "name": "test",
            "child": {"name": "child_test", "age": 10, "is_active": True},
        }
    ) == Config.model_validate(vars(args))


def test_multiple_config():
    class TwitterConfig(BaseModel):
        consumer_key: SecretStr | None = Field(None)
        consumer_secret: SecretStr | None = Field(None)
        access_token: SecretStr | None = Field(None)
        access_token_secret: SecretStr | None = Field(None)
        search_query: str = Field(description="Search query for Twitter API")

    class MisskeyConfig(BaseModel):
        host: str = Field(description="Misskey host")
        token: SecretStr = Field(description="Misskey token")
        search_query: str = Field(description="Search query for Misskey API")

    class Config(BaseModel):
        dest: str
        twitter: TwitterConfig
        misskey: MisskeyConfig

    parser = ArgumentParser()
    build_parser(parser, Config)

    a = parser._actions
    # Config.dest
    assert "--dest" in a[1].option_strings
    assert "dest" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].help is None
    # Config.twitter.consumer_key
    assert "--twitter.consumer-key" in a[2].option_strings
    # Config.twitter.consumer_secret
    assert "--twitter.consumer-secret" in a[3].option_strings
    # Config.twitter.access_token
    assert "--twitter.access-token" in a[4].option_strings
    # Config.twitter.access_token_secret
    assert "--twitter.access-token-secret" in a[5].option_strings
    # Config.twitter.search_query
    assert "--twitter.search-query" in a[6].option_strings
    # Config.misskey.host
    assert "--misskey.host" in a[7].option_strings
    # Config.misskey.token
    assert "--misskey.token" in a[8].option_strings
    # Config.misskey.search_query
    assert "--misskey.search-query" in a[9].option_strings
