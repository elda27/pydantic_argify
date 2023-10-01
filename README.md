# pydantic-argify
[![Python](https://img.shields.io/pypi/pyversions/pydantic-argify.svg)](https://pypi.org/project/pydantic-argify/)
[![PyPI version](https://badge.fury.io/py/pydantic-argify.svg)](https://badge.fury.io/py/pydantic-argify)
[![codecov](https://codecov.io/gh/elda27/pydantic_argify/branch/main/graph/badge.svg?token=GLqGNtE7Df)](https://codecov.io/gh/elda27/pydantic_argify)
[![Downloads](https://static.pepy.tech/badge/pydantic-argify)](https://pepy.tech/project/pydantic-argify)
[![License](https://img.shields.io/pypi/l/pydantic-argify.svg)](https://github.com/google/pydantic_argify/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Build ArgumentParser from pydantic model.

## What's difference with other projects.
This project is dedicated to crafting an argument parser based on the Pydantic model.
Unlike many other projects where the ArgumentParser functionality is concealed within the library, 
this tool aims to simplify its use, even in complex scenarios. 
For instance, handling nested sub-parsers like `aws s3 cp <some options>` 
or supporting nested Pydantic models has been a challenge in existing solutions. 
This library overcomes these limitations, allowing you to effortlessly incorporate intricate functionalities.

```python
```

## Example 1

```python
from argparse import ArgumentParser
from pydantic import BaseModel, Field
from pydantic_argify import build_parser

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
from pydantic_argify import build_parser

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

## Additional config
Behaviour of pydantic can be controlled via the `Config` class or extra arguments of `Field`.
`Config` is affected all fields.
Extra arguments of `Field` is affected specific field. 


<dl>
  <dt><code>cli_disable_prefix</code></dt>
  <dd>Prefix of argument of boolean type for `store_false`. Default to <code>--disable-</code></dd>

  <dt><code>cli_enable_prefix</code></dt>
  <dd>Prefix of argument of boolean type for `store_true`. Default to <code>--enable-</code></dd>
</dl>


## Future works

- [ ]: Options completion for bash
