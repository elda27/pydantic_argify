from typing import Dict, Union

from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class CliConfig(ConfigDict):
    cli_enable_prefix: Union[str, Dict[str, str]]
    cli_disable_prefix: Union[str, Dict[str, str]]


CliConfigDict = CliConfig


class EnvCliConfig(SettingsConfigDict):
    cli_enable_prefix: Union[str, Dict[str, str]]
    cli_disable_prefix: Union[str, Dict[str, str]]


EnvCliConfigDict = EnvCliConfig
