from argparse import Action, ArgumentParser
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Type, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import (
    SHAPE_DICT,
    SHAPE_LIST,
    SHAPE_MAPPING,
    SHAPE_SET,
    SHAPE_SINGLETON,
    SHAPE_TUPLE,
    ModelField,
    Undefined,
)
from pydantic.typing import is_literal_type, is_union


def get_model_field(model: Type[BaseModel]) -> Dict[str, ModelField]:
    """Get field info."""
    return {field.name: field for field in model.__fields__.values()}


def wrap_parser_default(func: Callable[[BaseModel], None], model_type: Type[BaseModel]):
    """Wrap parser default."""

    @wraps(func)
    def wrapper(args: Any):
        """Wrapper."""
        kwargs = vars(args)
        del kwargs["_command"]
        del kwargs["_func"]
        func(model_type.parse_obj(kwargs))

    return wrapper


def get_groupby_field_names(model: Type[BaseModel]) -> Dict[str, str]:
    """_summary_

    Parameters
    ----------
    model : Type[BaseModel]
        _description_

    Returns
    -------
    Dict[str, str]
        _description_
    """
    models = []
    for model_type in model.__mro__:
        if model_type is BaseModel:
            break
        models.append(model_type)
    result = {}
    for model_type in reversed(models):
        for name, _ in get_model_field(model_type).items():
            if name not in result:
                result[name] = model_type.__name__
    return result


class StoreKeywordParam(Action):
    """Store keyword parameters as a dict"""

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Any,
        values: Union[str, List[str]],
        option_strings=None,
    ):
        param_dict = getattr(namespace, self.dest, [])
        if param_dict is None:
            param_dict = {}
        if not isinstance(values, list):
            values = [values]

        for value in values:
            parts = value.split("=")
            if len(parts) < 2:
                raise ValueError(
                    "Wrong format of keyword parameters. Expected: key=value"
                )
            param_dict[parts[0]] = "=".join(parts[1:])
        setattr(namespace, self.dest, param_dict)


def build_parser(
    parser: ArgumentParser,
    model: Type[BaseModel],
    excludes: List[str] = [],
    auto_abbrev: bool = True,
    groupby: bool = True,
) -> ArgumentParser:
    """Create argument parser from pydantic model.

    Parameters
    ----------
    parser : ArgumentParser
        Argument parser object
    model : Type[BaseModel]
        BaseModel class
    excludes : List[str], optional
        Exclude field, by default []
    auto_abbrev : bool, optional
        Enable abbreviated parameter such as `-h`, by default True

    Returns
    -------
    ArgumentParser
        Argument parser object
    """
    groupby = get_groupby_field_names(model) if groupby else {}
    cache_parsers = {}
    exist_args = []
    for name, field in get_model_field(model).items():
        if name in excludes:
            continue

        kwargs = {}

        # Set option of multiple arguments
        kwargs["type"] = field.type_
        if field.shape in (SHAPE_LIST, SHAPE_SET):
            if field.required:
                kwargs["nargs"] = "+"
            else:
                kwargs["nargs"] = "*"
        elif field.shape in (SHAPE_DICT, SHAPE_MAPPING):
            kwargs["action"] = StoreKeywordParam
            kwargs["type"] = str
            if field.required:
                kwargs["nargs"] = "+"
            else:
                kwargs["nargs"] = "*"
        elif field.shape == SHAPE_TUPLE:
            args = get_args(field.type_)
            kwargs["type"] = args[0]
            kwargs["nargs"] = len(args)
        elif field.type_ is type and issubclass(field.type_, Enum):
            kwargs["choices"] = list(field.type_)
        elif is_literal_type(field.type_):
            del kwargs["type"]
            kwargs["choices"] = get_args(field.type_)
        elif is_union(get_origin(field.type_)):
            kwargs["type"] = str  # TODO: Support union type

        # Set default value
        if field.field_info.default is not Undefined:
            kwargs["default"] = field.field_info.default

        # Set abbreviated parameter
        args = [f"--{name.replace('_', '-')}"]
        if auto_abbrev:
            abbrev_arg = f"-{name[0]}"
            if abbrev_arg not in exist_args:
                args.append(abbrev_arg)
                exist_args.append(abbrev_arg)

        # Add arguments
        if name in groupby:
            group_name = groupby[name]
            if group_name not in cache_parsers:
                _parser = parser.add_argument_group(group_name)
                cache_parsers[group_name] = _parser
            else:
                _parser = cache_parsers[group_name]
        else:
            _parser = parser
        _parser.add_argument(
            *args,
            required=field.required,
            help=field.field_info.description,
            **kwargs,
        )
    return parser
