import argparse
import enum
import inspect
import functools
import sys

from types import FunctionType, ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Union

UNION_TYPE = type(Union[int, str])
Parser = Callable[[str], Any]


def main(*fns: Callable, description: str = None, module: ModuleType = None):
    """Parses command line arguments and call the chosen function with them.

    Arguments:
        - fns: list of function that can be launched from command line.
            Each function must have type hints, so that we know how to parse them.
        - description: help message to show on command line
        - module: will use the module to search functions and chose the description.
    """
    return make_main(*fns, module=module, description=description)(sys.argv[1:])


def single_main(fn: Callable):
    """Parses command line arguments and call the given function with them."""
    parser = func_argparser(fn)
    args = parser.parse_args(sys.argv[1:])
    return fn(**vars(args))


def make_main(*fns: Callable, module: ModuleType = None, description=None):
    """Creates a main method for the given module / list of functions.

    The returned method expects a list of command line arguments.
    """
    if module is None:
        module = sys.modules["__main__"]
    if description is None:
        description = module.__doc__
    if not fns:
        fns = tuple(resolve_public_fns(module))
    parser = multi_argparser(*fns, description=description)

    def main(args: List[str]):
        parsed_args = vars(parser.parse_args(args))
        command = parsed_args.pop("__command", None)
        if not command:
            return parser.print_usage()
        command(**parsed_args)

    return main


def resolve_public_fns(module: ModuleType = None) -> List[FunctionType]:
    if module is None:
        module = sys.modules["__main__"]

    # We only keep FunctionType because argspec works with those.
    # This will exclude builtins and C-funtions.
    fns = list(
        fn
        for n, fn in vars(module).items()
        if not n.startswith("_") and isinstance(fn, FunctionType)
    )
    return [fn for fn in fns if fn.__module__ == module.__name__]


def get_fn_description(fn: Callable) -> Optional[str]:
    """Returns the first line of a function doc string."""
    if not fn.__doc__:
        return None
    description = next((l for l in fn.__doc__.split("\n") if l.strip()), None)
    if not description:
        return None
    return description.strip()


def _get_arguments_description(
    fn: Callable, arguments: List[str], defaults: Dict[str, Any]
) -> Dict[str, str]:
    """Returns a description for each argument."""
    if not fn.__doc__:
        return {}
    descriptions = {}
    lines = list(filter(None, (l.strip("-* ") for l in fn.__doc__.split("\n"))))
    for a in arguments:
        # TODO: some arguments may have more than one line of documentation.
        doc = next((l[len(a) :].strip(" :") for l in lines if l.startswith(a)), None)
        default = defaults.get(a)
        # Don't show values defaulting to None.
        default_doc = f"(default={default})" if default is not None else None
        descriptions[a] = " ".join(filter(None, (doc, default_doc)))

    return descriptions


def multi_argparser(*fns: Callable, description: str = None) -> argparse.ArgumentParser:
    """Creates an ArgumentParser with one subparser for each given function."""
    parser = argparse.ArgumentParser(description=description, add_help=True)
    subparsers = parser.add_subparsers()
    for fn in fns:
        add_fn_subparser(fn, subparsers)

    return parser


def add_fn_subparser(fn: Callable, subparsers: argparse._SubParsersAction):
    p = subparsers.add_parser(fn.__name__, help=get_fn_description(fn))
    p.set_defaults(__command=fn)
    func_argparser(fn, p)


def _is_option_type(t: type) -> bool:
    return (
        isinstance(t, UNION_TYPE)
        and len(t.__args__) == 2
        and issubclass(t.__args__[1], type(None))
    )


def _parse_enum(enum: enum.EnumMeta, flags: List[str], value: str) -> enum.Enum:
    members = tuple(enum.__members__)
    # enum members might be case sensitive.
    if value in members:
        return enum[value]
    if value.upper() in members:
        return enum[value.upper()]

    # Mimick argparse error message for choices.
    # See https://github.com/python/cpython/blob/3.7/Lib/argparse.py#L2420
    msg = f"invalid choice: '{value}' (choose from {', '.join(members)})"
    action = argparse.Action(flags, "")
    raise argparse.ArgumentError(action, msg)


def _parse_union(parsers: List[Parser], union, flags: List[str], value: str) -> Any:
    for p in parsers:
        try:
            return p(value)
        except Exception:
            continue
    pretty = str(union)[len("typing.") :]
    msg = f"invalid {pretty} value: '{value}'"
    action = argparse.Action(flags, "")
    raise argparse.ArgumentError(action, msg)


def _get_parser(t, flags: List[str]):
    if isinstance(t, enum.EnumMeta):
        return functools.partial(_parse_enum, t, flags)
    elif _is_option_type(t):
        return _get_parser(t.__args__[0], flags)
    elif isinstance(t, UNION_TYPE):
        parsers = [
            _get_parser(st, flags)
            for st in t.__args__
            if not issubclass(st, type(None))
        ]
        return functools.partial(_parse_union, parsers, t, flags)
    else:
        return t


def func_argparser(
    fn: Callable, parser: Optional[argparse.ArgumentParser] = None
) -> argparse.ArgumentParser:
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
    args_desc = _get_arguments_description(fn, spec.args, defaults)

    prefixes: Set[str] = set()
    for a, t in spec.annotations.items():
        doc = args_desc.get(a)
        flags = [f"--{a}"]
        if a[0] not in prefixes:
            flags.insert(0, f"-{a[0]}")
            prefixes.add(a[0])

        if t is bool:
            d = defaults.get(a, False)
            parser.add_argument(*flags, default=d, action="store_true", help=doc)
            parser.add_argument(f"--no-{a}", dest=a, action="store_false")
            continue

        if _is_option_type(t):
            if a not in defaults:
                defaults[a] = None

        parser.add_argument(
            *flags,
            type=_get_parser(t, flags),
            default=defaults.get(a),
            required=a not in defaults,
            help=doc,
        )
    return parser
