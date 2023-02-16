from argparse import ArgumentParser

from pydantic import BaseModel, Field

from pydantic_argparse_builder import build_parser


class SubConfigA(BaseModel):
    string: str = Field(description="string parameter")
    integer: int = Field(description="integer parameter")


class SubConfigB(BaseModel):
    double: float = Field(description="a required string")
    integer: int = Field(0, description="a required integer")


parser = ArgumentParser()
subparsers = parser.add_subparsers()
build_parser(subparsers.add_parser("alpha"), SubConfigA)
build_parser(subparsers.add_parser("beta"), SubConfigB)
parser.print_help()
