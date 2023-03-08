# pydantic-argparse-builder

## What's this library

This library that automatically generates `ArgumentParser` from pydantic `BaseModel`.

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

Output:

```bash
usage: basic.py [-h] --string STRING --integer INTEGER

optional arguments:
  -h, --help            show this help message and exit

Config:
  --string STRING, -s STRING
                        a required string
  --integer INTEGER, -i INTEGER
                        a required integer
```

## How `pydantic-argparse-builder` differs from other libraries

The `pydantic-argparse` and `pydantic-cli` libraries can do similar things.

Both can create argument parsers on the basis of classes built with pydantic in the same way.
This is very convenient and improves the developer experience because many arguments can be implemented with VSCode completion by creating as an argument.

However, there are not easy to use SubParser, argument grouping, exclusive arguments, and so on in complicated ways because of the design that hides ArgumentParser internally.
In particular, nested SubParser usage (e.g., `aws s3 cp <argument>`) seems to be unsupported by any of the libraries.
