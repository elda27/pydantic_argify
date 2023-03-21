from typing import Dict, Union

from pydantic import BaseConfig, BaseSettings


class _CliConfig:
    cli_enable_prefix: Union[str, Dict[str, str]] = "--enable-"
    cli_disable_prefix: Union[str, Dict[str, str]] = "--disable-"


class CliConfig(BaseConfig, _CliConfig):
    pass


class EnvCliConfig(BaseSettings.Config, _CliConfig):
    pass
