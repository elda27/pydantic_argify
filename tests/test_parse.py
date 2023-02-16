from argparse import ArgumentParser
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from pydantic_argparse import create_parser
from pydantic_argparse.parse import get_groupby_field_names


def test_tuple():
    class Config(BaseModel):
        param: Tuple[str, str, str]

    parser = ArgumentParser()
    create_parser(parser, Config)

    # param
    a = parser._actions
    assert "--param" in a[1].option_strings
    assert "param" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].nargs == 3
    assert a[1].help is None

    args = parser.parse_args(
        [
            "--param",
            "value1",
            "value2",
            "value3",
        ]
    )
    assert Config(
        **{
            "param": ("value1", "value2", "value3"),
        }
    ) == Config.parse_obj(vars(args))


def test_union():
    class Config(BaseModel):
        param: Union[str, int]

    parser = ArgumentParser()
    create_parser(parser, Config)

    # param
    a = parser._actions
    assert "--param" in a[1].option_strings
    assert "param" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].nargs is None
    assert a[1].help is None

    args = parser.parse_args(
        [
            "--param",
            "value",
        ]
    )
    assert Config(
        **{
            "param": "value",
        }
    ) == Config.parse_obj(vars(args))

    args = parser.parse_args(
        [
            "--param",
            "10",
        ]
    )
    assert Config(
        **{
            "param": 10,
        }
    ) == Config.parse_obj(vars(args))


def test_argparse():
    class Config(BaseModel):
        param: str
        param_2: Optional[str]
        param_3: Optional[str] = None
        param_4: List[str] = Field(["value"], description="description of the param_4")
        param_5: List[str] = Field(description="description of the param_4")

    parser = ArgumentParser()
    create_parser(parser, Config)
    a = parser._actions

    # param
    assert "--param" in a[1].option_strings
    assert "param" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].nargs is None
    assert a[1].help is None

    # param_2
    assert "--param-2" in a[2].option_strings
    assert "param_2" == a[2].dest
    assert a[2].type is str
    assert a[2].default is None
    assert not a[2].required
    assert a[2].nargs is None
    assert a[2].help is None

    # param_3
    assert "--param-3" in a[3].option_strings
    assert "param_3" == a[3].dest
    assert a[3].type is str
    assert a[3].default is None
    assert not a[3].required
    assert a[3].nargs is None
    assert a[3].help is None

    # param_4
    assert "--param-4" in a[4].option_strings
    assert "param_4" == a[4].dest
    assert a[4].type is str
    assert a[4].default == ["value"]
    assert not a[4].required
    assert a[4].nargs == "*"
    assert a[4].help == "description of the param_4"

    # param_5
    assert "--param-5" in a[5].option_strings
    assert "param_5" == a[5].dest
    assert a[5].type is str
    assert a[5].default is None
    assert a[5].required
    assert a[5].nargs == "+"
    assert a[5].help == "description of the param_4"

    # Test parse
    args = parser.parse_args(
        [
            "--param",
            "value",
            "--param-2",
            "value",
            "--param-4",
            "value",
            "value",
            "--param-5",
            "value",
            "value",
        ]
    )
    assert Config(
        **{
            "param": "value",
            "param_2": "value",
            "param_3": None,
            "param_4": ["value", "value"],
            "param_5": ["value", "value"],
        }
    ) == Config.parse_obj(vars(args))


def test_get_groupby_field_names():
    class Config(BaseModel):
        param: str
        param_2: Optional[str]
        param_3: Optional[str] = None

    class Config2(Config):
        param_4: List[str] = Field(["value"], description="description of the param_4")
        param_5: List[str] = Field(description="description of the param_4")

    fields = get_groupby_field_names(Config2)
    assert fields == {
        "param": "Config",
        "param_2": "Config",
        "param_3": "Config",
        "param_4": "Config2",
        "param_5": "Config2",
    }


def test_argparse_with_group():
    class Config(BaseModel):
        param: str
        param_2: Optional[str]
        param_3: Optional[str] = None

    class Config2(Config):
        param_4: List[str] = Field(["value"], description="description of the param_4")
        param_5: List[str] = Field(description="description of the param_4")

    parser = ArgumentParser()
    create_parser(parser, Config2)
    a = parser._actions

    assert len(parser._action_groups) == 4

    # param
    assert "--param" in a[1].option_strings
    assert "param" == a[1].dest
    assert a[1].type is str
    assert a[1].default is None
    assert a[1].required
    assert a[1].nargs is None
    assert a[1].help is None

    # param_2
    assert "--param-2" in a[2].option_strings
    assert "param_2" == a[2].dest
    assert a[2].type is str
    assert a[2].default is None
    assert not a[2].required
    assert a[2].nargs is None
    assert a[2].help is None

    # param_3
    assert "--param-3" in a[3].option_strings
    assert "param_3" == a[3].dest
    assert a[3].type is str
    assert a[3].default is None
    assert not a[3].required
    assert a[3].nargs is None
    assert a[3].help is None

    # param_4
    assert "--param-4" in a[4].option_strings
    assert "param_4" == a[4].dest
    assert a[4].type is str
    assert a[4].default == ["value"]
    assert not a[4].required
    assert a[4].nargs == "*"
    assert a[4].help == "description of the param_4"

    # param_5
    assert "--param-5" in a[5].option_strings
    assert "param_5" == a[5].dest
    assert a[5].type is str
    assert a[5].default is None
    assert a[5].required
    assert a[5].nargs == "+"
    assert a[5].help == "description of the param_4"

    # Test parse
    args = parser.parse_args(
        [
            "--param",
            "value",
            "--param-2",
            "value",
            "--param-4",
            "value",
            "value",
            "--param-5",
            "value",
            "value",
        ]
    )
    assert Config(
        **{
            "param": "value",
            "param_2": "value",
            "param_3": None,
            "param_4": ["value", "value"],
            "param_5": ["value", "value"],
        }
    ) == Config.parse_obj(vars(args))
