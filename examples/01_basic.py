from argparse import ArgumentParser

from pydantic import BaseModel, Field

from pydantic_argify import build_parser


class Config(BaseModel):
    string: str = Field(description="string parameter")
    integer: int = Field(description="integer parameter")


parser = ArgumentParser()
build_parser(parser, Config)
parser.print_help()
