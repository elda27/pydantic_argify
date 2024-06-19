from pydantic import BaseModel, Field

from pydantic_argify import main, sub_command


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
