# pydantic-argparse

Build ArgumentParser from pydantic model.

## What's difference with other projects.

This project focuses on creating an argument parser from the pydantic model.
You can easily add a sub parser.

## Example 1

```python
from argparse import ArgumentParser
from pydantic import BaseModel, Field
from pydantic_argparse_builder import build_parser

class Config(BaseModel):
    string: str = Field(description="string parameter")
    integer: int = Field(description="integer parameter")

parser = ArgumentParser()
build_parser(parser)
parser.print_help()
```

```
usage: basic.py [-h] --string STRING --integer INTEGER

optional arguments:
  -h, --help            show this help message and exit

Config:
  --string STRING, -s STRING
                        a required string
  --integer INTEGER, -i INTEGER
                        a required integer
```

## Example 2

```python
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
```

```
usage: sub_parser.py [-h] {alpha,beta} ...

positional arguments:
  {alpha,beta}

optional arguments:
  -h, --help    show this help message and exit
```
