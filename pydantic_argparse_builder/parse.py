from argparse import Action, ArgumentParser
from copy import deepcopy
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Type, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import (
    SHAPE_DICT,
    SHAPE_LIST,
    SHAPE_MAPPING,
    SHAPE_SET,
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
    """Get field names for groups

    Parameters
    ----------
    model : Type[BaseModel]
        model class

    Returns
    -------
    Dict[str, str]
        pair of field name and group name
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
    auto_truncate: bool = True,
    groupby_inherit: bool = True,
    exclude_truncated_args: List[str] = ["-h"],
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
    auto_truncate : bool, optional
        Enable truncated parameter such as `-h`, by default True
    groupby_inherit: bool, optional
        If True, inherited basemodels are grouped by class name, by default True
    exclude_truncated_args: List[str], optional
        Exclude truncated arguments, by default ["-h"]

    Returns
    -------
    ArgumentParser
        Argument parser object
    """
    groups = get_groupby_field_names(model) if groupby_inherit else {}
    cache_parsers = {}
    exist_truncate_args = deepcopy(exclude_truncated_args)
    for name, field in get_model_field(model).items():
        if name in excludes:
            continue

        kwargs = {}

        # Set option of multiple arguments
        kwargs.update(**_parse_shape_args(name, field))

        # Set default value
        if field.field_info.default is not Undefined:
            kwargs["default"] = field.get_default()

        # If groupby is enabled, create a new parser for each group
        if name in groups:
            group_name = groups[name]
            if group_name not in cache_parsers:
                _parser = parser.add_argument_group(group_name)
                cache_parsers[group_name] = _parser
            else:
                _parser = cache_parsers[group_name]
        else:
            _parser = parser

        kwargs["help"] = field.field_info.description
        # Set option args
        if field.type_ is bool:
            # Special case for boolean
            del kwargs["type"]
            kwargs["dest"] = name

            if field.required:
                # Create both enable and disable option
                _add_both_options(_parser, name, field, kwargs)
            else:
                # Create either one option.
                _add_either_option(_parser, name, field, kwargs)
        else:
            # default case for other types
            args = [f"--{name.replace('_', '-')}"]
            # Set truncateiated parameter
            if auto_truncate:
                truncate_arg = f"-{name[0]}"
                if truncate_arg not in exist_truncate_args:
                    args.append(truncate_arg)
                    exist_truncate_args.append(truncate_arg)

            _parser.add_argument(
                *args,
                required=field.required,
                **kwargs,
            )

    return parser


def get_cli_names(name: str, field: ModelField, prefix: str = "") -> List[str]:
    """Create cli string from field name.

    Parameters
    ----------
    name : str
        field name
    field : ModelField
        field object
    prefix : str, optional
        prefix of the default arguments, by default ""

    Returns
    -------
    List[str]
        list of cli arguments
    """
    names = field.field_info.extra.get("cli", None)
    if names is None:
        names = [prefix + name.replace("_", "-")]
        if field.has_alias:
            names.append(prefix + field.alias.replace("_", "-"))
    return names


def _parse_shape_args(name: str, field: ModelField) -> dict:
    kwargs = {}
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
    return kwargs


def _add_both_options(
    parser: ArgumentParser,
    name: str,
    field: ModelField,
    kwargs: Dict[str, Any],
):
    mutual = parser.add_mutually_exclusive_group(required=True)

    args = get_cli_names(name, field, "--enable-")
    kwargs["action"] = "store_true"
    mutual.add_argument(
        *args,
        **kwargs,
    )
    args = get_cli_names(name, field, "--disable-")
    kwargs["action"] = "store_false"
    mutual.add_argument(
        *args,
        **kwargs,
    )


def _add_either_option(
    parser: ArgumentParser,
    name: str,
    field: ModelField,
    kwargs: Dict[str, Any],
):
    if kwargs["default"]:
        args = get_cli_names(name, field, prefix="--disable-")
        kwargs["action"] = "store_false"
    else:
        args = get_cli_names(name, field, prefix="--enable-")
        kwargs["action"] = "store_true"
    parser.add_argument(
        *args,
        **kwargs,
    )
