from pydantic import BaseModel, Field

from pydantic_argify import command, main


class ChildConfig(BaseModel):
    name: str
    age: int = Field(10)
    is_active: bool


class Config(BaseModel):
    name: str
    child: ChildConfig


@command
def run(config: Config):
    print(config)


if __name__ == "__main__":
    main()
