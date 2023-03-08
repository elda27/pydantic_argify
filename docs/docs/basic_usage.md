# Basic usage

```python title="01_basic.py"
from argparse import ArgumentParser
from pydantic import BaseModel, Field
from pydantic_argparse_builder import build_parser

class Config(BaseModel):
    string: str = Field(description="string parameter")
    integer: int = Field(description="integer parameter")

parser = ArgumentParser()
build_parser(parser, Config)
args = parser.parse_args()
print(Config(**vars(args)))
```

```bash
$> python example.py --string str --integer 10
string='str' integer=10
```
