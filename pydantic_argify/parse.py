import json
import types
import typing
from argparse import Action, ArgumentParser
from copy import deepcopy
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Type,
    Union,
    get_args,
    get_origin,
    overload,
)

from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo, PydanticUndefined


class NestedFieldStoreAction(Action):
    def __init__(self, option_strings, dest: str, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        if self.dest is None:
            if isinstance(option_strings, str):
                self._field_names = option_strings.strip("-").split(".")
            elif isinstance(option_strings, (list, tuple)):
                self._field_names = option_strings[0].strip("-").split(".")
            else:
                raise ValueError("Unknown dest format")
        else:
            self._field_names = self.dest.split(".")

    def __call__(
        self, parser: ArgumentParser, namespace: Any, values, option_string=None
    ):

        field = getattr(namespace, self._field_names[0], None)
        if field is None:
            setattr(namespace, self._field_names[0], {})
            field = getattr(namespace, self._field_names[0])
        for field_name in self._field_names[1:]:
            field[field_name] = self.type(values)


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


if typing.TYPE_CHECKING:

    @overload
    def build_parser(
        parser: ArgumentParser,
        model: Type[BaseModel] | None,
        *,
        excludes: List[str] = [],
        auto_truncate: bool = True,
        groupby_inherit: bool = True,
        exclude_truncated_args: List[str] = ["-h"],
        parse_nested_model: bool = True,
        naming_separator: str = "-",
    ) -> ArgumentParser: ...

    @overload
    def build_parser(
        parser: ArgumentParser,
        model: Type[BaseModel] | None,
        **kwargs,
    ) -> ArgumentParser: ...


def build_parser(
    parser: ArgumentParser, model: Type[BaseModel] | None, **kwargs
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
        return build_parser_impl(parser, model, **kwargs)
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
    name_prefix: str | None = None,
    naming_separator: str = "-",
    action: type[Action] | None = None,
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
        Enable truncated parameter such as `-h` from a field of `have_fun`, by default True
    groupby_inherit: bool, optional
        If True, inherited basemodels are grouped by class name, by default True
    exclude_truncated_args: List[str], optional
        Exclude truncated arguments, by default ["-h"]
        If list contains `-h`, `--have-fun` don't create truncated argument `-h` from have_fun.
    parse_nested_model: bool
        If True, nested model is also parsed, by default True
        ```python
        class NestedModel(BaseModel):
            nested_field: str
        class Model(BaseModel):
            nested: NestedModel
        ```
        In this case, `--nested.nested-field` is created.
    name_prefix: str | None, optional
        Prefix of the argument name, by default None
        --{name_prefix}{field_name} is used if name_prefix is not None
    naming_separator: str, optional
        Separator of the argument name, by default "-"
    action: Action | None, optional
        Action object for argument parser, by default None
    Returns
    -------
    ArgumentParser
        Argument parser object
    """
    model_config = model.model_config
    groups = get_groupby_field_names(model) if groupby_inherit else {}
    cache_parsers = {}
    exist_truncate_args = exclude_truncated_args
    _parser: Any
    for name, field in get_model_field(model).items():
        if name in excludes:
            continue

        # If nested model is enabled, parse it
        if (
            parse_nested_model
            and isinstance(field.annotation, type)
            and issubclass(field.annotation, BaseModel)
        ):
            orig_name_prefix = None
            if name_prefix is not None:
                name_prefix = ".".join([name_prefix, name]) + "."
            else:
                name_prefix = name + "."
            build_parser_impl(
                parser,
                field.annotation,
                excludes=excludes,
                groupby_inherit=True,
                exclude_truncated_args=exclude_truncated_args,
                parse_nested_model=parse_nested_model,
                name_prefix=name_prefix,
                naming_separator=naming_separator,
                action=NestedFieldStoreAction,
            )
            name_prefix = orig_name_prefix
            continue

        kwargs: dict[str, Any] = {"action": action}

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

        kwargs["help"] = field.description or field.title
        # Set option args, if not exists extra action
        if kwargs.get("action") is None and field.annotation is bool:
            # Special case for boolean
            del kwargs["type"]
            kwargs["dest"] = name

            if field.is_required():
                # Create both enable and disable option
                _add_both_options(
                    _parser,
                    name,
                    field,
                    kwargs,
                    config=model.model_config,
                    naming_separator=naming_separator,
                )
            else:
                # Create either one option.
                _add_either_option(
                    _parser,
                    name,
                    field,
                    kwargs,
                    config=model.model_config,
                    naming_separator=naming_separator,
                )
        else:
            # default case for other types
            args = get_cli_names(
                name,
                field,
                model_config,
                naming_separator=naming_separator,
                prefix=f"--{name_prefix or ''}",
            )
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
    name: str,
    field: FieldInfo,
    model_config: ConfigDict,
    naming_separator: str,
    prefix: str = "",
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
            names.append(prefix + field.alias.replace("_", naming_separator))
        names.append(prefix + name.replace("_", naming_separator))
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
    naming_separator: str,
):
    mutual = parser.add_mutually_exclusive_group(required=True)

    args = get_cli_names(
        name,
        field,
        config,
        naming_separator=naming_separator,
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
        naming_separator=naming_separator,
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
    naming_separator: str,
):
    if kwargs["default"]:
        args = get_cli_names(
            name,
            field,
            config,
            naming_separator=naming_separator,
            prefix=_get_extra(
                field, config, "cli_disable_prefix", f"--disable{naming_separator}"
            ),
        )
        kwargs["action"] = "store_false"
    else:
        args = get_cli_names(
            name,
            field,
            config,
            naming_separator=naming_separator,
            prefix=_get_extra(
                field, config, "cli_enable_prefix", f"--enable{naming_separator}"
            ),
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
