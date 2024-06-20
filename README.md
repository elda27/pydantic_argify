# pydantic-argify
[![Python](https://img.shields.io/pypi/pyversions/pydantic-argify.svg)](https://pypi.org/project/pydantic-argify/)
[![PyPI version](https://badge.fury.io/py/pydantic-argify.svg)](https://badge.fury.io/py/pydantic-argify)
[![codecov](https://codecov.io/gh/elda27/pydantic_argify/branch/main/graph/badge.svg?token=GLqGNtE7Df)](https://codecov.io/gh/elda27/pydantic_argify)
[![Downloads](https://static.pepy.tech/badge/pydantic-argify)](https://pepy.tech/project/pydantic-argify)
[![License](https://img.shields.io/pypi/l/pydantic-argify.svg)](https://github.com/google/pydantic_argify/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Build ArgumentParser from pydantic model.

## Getting started
### High level api

See ./examples/00_getting_started.py
```python
from pydantic import BaseModel, Field
from pydantic_argify import sub_command, main

class ConfigCommand1(BaseModel):
    string: str = Field(description="string parameter")
    integer: int = Field(description="integer parameter")

class ConfigCommand2(BaseModel):
    string: str = Field(description="string parameter")

@sub_command("command1")
def command1(config: ConfigCommand1):
    print(config)

@sub_command("command2")
def command2(config: ConfigCommand2):
    print(config)

if __name__ == "__main__":
    main()
```

```bash
$ poetry run python -m examples.00_getting_started command1 -h
usage: 00_getting_started.py command1 [-h] --string STRING --integer INTEGER

options:
  -h, --help            show this help message and exit

ConfigCommand1:
  --string STRING, -s STRING
                        string parameter
  --integer INTEGER, -i INTEGER
                        integer parameter
```

### Low level api
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

## What's difference with other projects.
This project is dedicated to crafting an argument parser based on the Pydantic model.
Unlike many other projects where the ArgumentParser functionality is concealed within the library, 
this tool aims to simplify its use, even in complex scenarios. 
For instance, handling nested sub-parsers like `aws s3 cp <some options>` 
or supporting nested Pydantic models has been a challenge in existing solutions. 
This library overcomes these limitations, allowing you to effortlessly incorporate intricate functionalities.

### Example 
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

## Nested config
See: ./examples/06_nested_field

```bash
$ python -m examples.06_nested_field -h
usage: 06_nested_field.py [-h] --name NAME --child.name CHILD.NAME [--child.age CHILD.AGE] --child.is-active CHILD.IS_ACTIVE

options:
  -h, --help            show this help message and exit

Config:
  --name NAME, -n NAME

ChildConfig:
  --child.name CHILD.NAME, -c CHILD.NAME
  --child.age CHILD.AGE
  --child.is-active CHILD.IS_ACTIVE
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
