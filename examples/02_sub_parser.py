from argparse import ArgumentParser

from pydantic import BaseModel, Field

from pydantic_argparse_builder import build_parser


class SubConfigA(BaseModel):
    string: str = Field(description="string parameter")
    integer: int = Field(description="integer parameter")


class SubConfigB(BaseModel):
    double: float = Field(description="a required string")
    integer: int = Field(0, description="a required integer")


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    alpha_parser = subparsers.add_parser("alpha")
    build_parser(alpha_parser, SubConfigA)
    alpha_parser.set_defaults(_command="A")
    build_parser(subparsers.add_parser("beta"), SubConfigB)

    beta_parser = subparsers.add_parser("beta")
    build_parser(beta_parser, SubConfigB)
    beta_parser.set_defaults(_command="B")
    parser.set_defaults(_command="help")

    args = parser.parse_args()

    if args._command == "A":
        command_a(config=SubConfigA(**vars(args)))
    elif args._command == "B":
        command_b(config=SubConfigA(**vars(args)))
    else:
        parser.print_help()


def command_a(config: SubConfigA):
    print(config)


def command_b(config: SubConfigB):
    print(config)


if __name__ == "__main__":
    main()
