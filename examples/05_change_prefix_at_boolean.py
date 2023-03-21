from argparse import ArgumentParser

from pydantic import BaseModel, Field

from pydantic_argparse_builder import CliConfig, build_parser


class Config(BaseModel):
    param: bool
    switch: bool = Field(
        ..., cli_enable_prefix="--true-", cli_disable_prefix="--false-"
    )

    class Config(CliConfig):
        cli_enable_prefix = "--on-"
        cli_disable_prefix = "--off-"


parser = ArgumentParser()
build_parser(parser, Config)
print(parser.parse_args())
