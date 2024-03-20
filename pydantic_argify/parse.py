from argparse import Action, ArgumentParser
from copy import deepcopy
from enum import Enum
from typing import Any, Dict, List, Type, Union, get_args, get_origin, Literal, Mapping

from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo, PydanticUndefined
import types

def get_model_field(model: Type[BaseModel]) -> Dict[str, FieldInfo]:
    """Get field info."""
    return {name: field for name, field in model.model_fields.items()}


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
        param_dict = getattr(namespace, self.dest)
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
    parser: ArgumentParser, model: Type[BaseModel] | None
) -> ArgumentParser:
    """Create argument parser from pydantic model.

    Parameters
    ----------
    parser : ArgumentParser
        argument parser object
    model : Type[BaseModel] | None
        BaseModel class

    Returns
    -------
    ArgumentParser
        argument parser object
    """
    if model is not None:
        # build parser from model
        return build_parser_impl(parser, model)
    else:
        # do nothing
        return parser


def build_parser_impl(
    parser: ArgumentParser,
    model: Type[BaseModel],
    excludes: List[str] = [],
    auto_truncate: bool = True,
    groupby_inherit: bool = True,
    exclude_truncated_args: List[str] = ["-h"],
    parse_nested_model: bool = True,
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
    parse_nested_model: bool
        If True, nested model is also parsed, by default True
    Returns
    -------
    ArgumentParser
        Argument parser object
    """
    model_config = model.model_config
    groups = get_groupby_field_names(model) if groupby_inherit else {}
    cache_parsers = {}
    exist_truncate_args = deepcopy(exclude_truncated_args)
    _parser: Any
    for name, field in get_model_field(model).items():
        if name in excludes:
            continue

        if (
            parse_nested_model
            and isinstance(field.annotation, type)
            and issubclass(field.annotation, BaseModel)
        ):
            build_parser_impl(
                parser,
                field.annotation,
                excludes=excludes,
                groupby_inherit=True,
                exclude_truncated_args=exclude_truncated_args,
                parse_nested_model=parse_nested_model,
            )
            continue

        kwargs: dict[str, Any] = {}

        # Set option of multiple arguments
        kwargs.update(**_parse_shape_args(name, field))

        # Set default value
        if field.default is not PydanticUndefined:
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

        kwargs["help"] = field.description
        # Set option args
        if field.annotation is bool:
            # Special case for boolean
            del kwargs["type"]
            kwargs["dest"] = name

            if field.is_required():
                # Create both enable and disable option
                _add_both_options(
                    _parser, name, field, kwargs, config=model.model_config
                )
            else:
                # Create either one option.
                _add_either_option(
                    _parser, name, field, kwargs, config=model.model_config
                )
        else:
            # default case for other types
            args = get_cli_names(name, field, model_config, prefix="--")
            # Set truncateiated parameter
            if auto_truncate:
                truncate_arg = f"-{args[0].strip('-')[0]}"
                if truncate_arg not in exist_truncate_args:
                    args.append(truncate_arg)
                    exist_truncate_args.append(truncate_arg)

            _parser.add_argument(
                *args,
                required=field.is_required(),
                **kwargs,
            )

    return parser


def get_cli_names(
    name: str, field: FieldInfo, model_config: ConfigDict, prefix: str = ""
) -> List[str]:
    """Create cli string from field name.

    Parameters
    ----------
    name : str
        field name
    field : FieldInfo
        field object
    prefix : str, optional
        prefix of the default arguments, by default ""

    Returns
    -------
    List[str]
        list of cli arguments
    """
    names = _get_extra(field, model_config, "cli", None)
    if names is None:
        names = []
        if field.alias is not None:
            names.append(prefix + field.alias.replace("_", "-"))
        names.append(prefix + name.replace("_", "-"))
    return names


def _parse_shape_args(name: str, field: FieldInfo) -> dict:
    kwargs: dict[str, Any] = {}
    kwargs["type"] = field.annotation
    origin = get_origin(field.annotation)
    # field.discriminator
    if field.annotation is None:
        # No annotation provieded but this case is not expected.
        kwargs["type"] = str
    elif origin is list or origin is set:
        # list
        kwargs["type"] = get_args(field.annotation)[0]
        if field.is_required():
            kwargs["nargs"] = "+"
        else:
            kwargs["nargs"] = "*"
    elif origin is dict or origin is Mapping:
        # dictionary
        kwargs["action"] = StoreKeywordParam
        kwargs["type"] = str
        if field.is_required():
            kwargs["nargs"] = "+"
        else:
            kwargs["nargs"] = "*"
    elif origin is tuple:
        # tuple
        args = get_args(field.annotation)
        kwargs["type"] = args[0]
        kwargs["nargs"] = len(args)
    elif origin is type and issubclass(field.annotation, Enum):
        # enum
        kwargs["choices"] = list(field.annotation)
    elif origin is Literal:
        del kwargs["type"]
        kwargs["choices"] = get_args(field.annotation)
    elif origin is Union or isinstance(field.annotation, types.UnionType):
        kwargs["type"] = str  # TODO: Support union type
    return kwargs


def _add_both_options(
    parser: ArgumentParser,
    name: str,
    field: FieldInfo,
    kwargs: Dict[str, Any],
    config: ConfigDict,
):
    mutual = parser.add_mutually_exclusive_group(required=True)

    args = get_cli_names(
        name,
        field,
        config,
        prefix=_get_extra(field, config, "cli_enable_prefix", "--enable-"),
    )
    kwargs["action"] = "store_true"
    mutual.add_argument(
        *args,
        **kwargs,
    )
    args = get_cli_names(
        name,
        field,
        config,
        prefix=_get_extra(field, config, "cli_disable_prefix", "--disable-"),
    )
    kwargs["action"] = "store_false"
    mutual.add_argument(
        *args,
        **kwargs,
    )


def _add_either_option(
    parser: ArgumentParser,
    name: str,
    field: FieldInfo,
    kwargs: Dict[str, Any],
    config: ConfigDict,
):
    if kwargs["default"]:
        args = get_cli_names(
            name,
            field,
            config,
            prefix=_get_extra(field, config, "cli_disable_prefix", "--disable-"),
        )
        kwargs["action"] = "store_false"
    else:
        args = get_cli_names(
            name,
            field,
            config,
            prefix=_get_extra(field, config, "cli_enable_prefix", "--enable-"),
        )
        kwargs["action"] = "store_true"
    parser.add_argument(
        *args,
        **kwargs,
    )


def _get_extra(
    field: FieldInfo, config: ConfigDict, key: str, default: Any = None
) -> Any:
    """Get extra field from config.

    Args:
        field (FieldInfo): Field object
        config (ConfigDict): Config object
        key (str): key name
        default (Any, optional): default value if not exists. Defaults to None.

    Returns:
        Any: value of the key
    """
    if field.json_schema_extra is None:
        return config.get(key, default)
    else:
        return field.json_schema_extra.get(key, default)
