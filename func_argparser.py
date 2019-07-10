import argparse
import inspect
import sys

from types import FunctionType, ModuleType
from typing import Callable, List, Optional, Set

OPTIONAL_TYPE = type(Optional[int])


def run_main(*fns: Callable, description: str = None, module: ModuleType = None):
    """Parses command line arguments and call the chosen function with them.

    Arguments:
        - fns: list of function that can be launched from command line.
            Each function must have type hints, so that we know how to parse them.
        - description: help message to show on command line
        - module: will use the module to search functions and chose the description.
    """
    make_main(*fns, module=module, description=description)(sys.argv[1:])


def make_main(*fns: Callable, module=None, description=None):
    """Creates a main method for the given module / list of functions.

    The returned method expects a list of command line arguments.
    """
    if module is None:
        module = sys.modules["__main__"]
    if description is None:
        description = module.__doc__

    if not fns:
        fns = [
            fn
            for n, fn in vars(module).items()
            if not n.startswith("_") and isinstance(fn, FunctionType)
        ]
    parser = multi_argparser(*fns, description=description)

    def main(args: List[str]):
        parsed_args = vars(parser.parse_args(args))
        command = parsed_args.pop("__command", None)
        if not command:
            return parser.print_usage()
        command(**parsed_args)

    return main


def get_fn_description(fn: Callable) -> Optional[str]:
    """Returns the first line of a function doc string."""
    if not fn.__doc__:
        return None
    description = next((l for l in fn.__doc__.split("\n") if l.strip()), None)
    if not description:
        return None
    return description.strip()


def multi_argparser(*fns: Callable, description=None) -> argparse.ArgumentParser:
    """Creates an ArgumentParser with one subparser for each given function."""
    parser = argparse.ArgumentParser(description=description, add_help=True)
    subparsers = parser.add_subparsers()
    for fn in fns:
        p = subparsers.add_parser(
            fn.__name__, help=get_fn_description(fn), usage=fn.__doc__
        )
        p.set_defaults(__command=fn)
        fn_argparser(fn, p)

    return parser


def fn_argparser(
    fn: Callable, parser: Optional[argparse.ArgumentParser] = None
) -> Optional[argparse.ArgumentParser]:
    """Creates an ArgumentParser for the given function."""
    if not parser:
        parser = argparse.ArgumentParser(description=get_fn_description(fn))

    spec = inspect.getfullargspec(fn)

    for a in spec.args:
        assert a in spec.annotations, f"Need a type annotation for argument {a} of {fn}"

    if spec.defaults:
        defaults = dict(zip(reversed(spec.args), reversed(spec.defaults)))
    else:
        defaults = {}

    prefixes: Set[str] = set()
    for a, t in spec.annotations.items():
        if t == bool:
            assert not defaults.get(
                a, False
            ), f"Boolean arg {a} of {fn} must default to False"
            parser.add_argument(f"--{a}", action="store_true")
            continue
        if isinstance(t, OPTIONAL_TYPE):
            # t can also be a union, but we don't support them yet
            assert t.__args__[1] == type(
                None
            ), f"Unsupported type {t} for argument {a} of {fn}"  # noqa: E721
            t = t.__args__[0]
            if a not in defaults:
                defaults[a] = None

        flags = [f"--{a}"]
        if a[0] not in prefixes:
            flags.insert(0, f"-{a[0]}")
            prefixes.add(a[0])
        parser.add_argument(
            *flags, type=t, default=defaults.get(a), required=a not in defaults
        )
    return parser
