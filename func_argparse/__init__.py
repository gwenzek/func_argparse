import argparse
import enum
import inspect
import functools
import sys

from types import FunctionType, ModuleType
from typing import Any, Callable, Dict, List, Optional, Set, Union

_GenericAlias = type(Union[int, str])
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


def get_documentation(fn: Callable) -> List[str]:
    fn_doc = fn.__doc__.split("\n") if fn.__doc__ else []
    init_doc: List[str] = []
    if isinstance(fn, type):
        init_docstr = fn.__init__.__doc__  # type: ignore
        if init_docstr:
            init_doc = init_docstr.split()

    return [l.strip() for l in init_doc + fn_doc if l.strip()]


def get_fn_description(fn: Callable) -> Optional[str]:
    """Returns the first line of a function doc string."""
    doc = get_documentation(fn)
    return doc[0] if doc else None


def _get_arguments_description(
    fn: Callable, signature: inspect.FullArgSpec, defaults: Dict[str, Any]
) -> Dict[str, str]:
    """Returns a description for each argument."""
    lines = get_documentation(fn)
    if not lines:
        return {}
    descriptions = {}
    lines = list(filter(None, (l.strip("-* ") for l in lines)))
    for a in signature.args:
        # TODO: some arguments may have more than one line of documentation.
        doc = next((l[len(a) :].strip(" :") for l in lines if l.startswith(a)), None)
        default = defaults.get(a)

        # Don't show values defaulting to None.
        default_doc = f"(default={default})" if default is not None else None

        # Only talk about the --no flag if the default is True
        if signature.annotations.get(a) == bool and default is True:
            default_doc = f"(default={default}, --no-{a} to disable)"

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


def _is_option_type(t: Callable) -> bool:
    if not isinstance(t, _GenericAlias):
        return False
    return (
        t.__origin__ == Union
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


def _get_parser(t: Parser, flags: List[str]) -> Parser:
    # TODO: this abstraction doesn't hold off, we often need to modify the
    # underlying 'action' to be consistent with the parser.
    # this function should receive a reasonable action and only change the parts
    # needed for this type.
    if isinstance(t, enum.EnumMeta):
        return functools.partial(_parse_enum, t, flags)
    elif _is_option_type(t):
        assert isinstance(t, _GenericAlias)
        return _get_parser(t.__args__[0], flags)
    elif isinstance(t, _GenericAlias) and t.__origin__ is Union:
        parsers = [
            _get_parser(st, flags)
            for st in t.__args__
            if not issubclass(st, type(None))
        ]
        return functools.partial(_parse_union, parsers, t, flags)
    elif isinstance(t, _GenericAlias) and t.__origin__ is list:
        return _get_parser(t.__args__[0], flags)
    else:
        return t


def func_argparser(
    fn: Callable, parser: Optional[argparse.ArgumentParser] = None
) -> argparse.ArgumentParser:
    """Creates an ArgumentParser for the given function."""
    if not parser:
        parser = argparse.ArgumentParser(description=get_fn_description(fn))

    spec = inspect.getfullargspec(fn)
    args = spec.args
    if isinstance(fn, type):
        # Ignore `self` from `__init__` method.
        args = args[1:]
    for a in args:
        assert a in spec.annotations, f"Need a type annotation for argument {a} of {fn}"

    if spec.defaults:
        defaults = dict(zip(reversed(args), reversed(spec.defaults)))
    else:
        defaults = {}
    args_desc = _get_arguments_description(fn, spec, defaults)

    # One letter arguments are given the short flags.
    prefixes: Set[str] = set(a for a in args if len(a) == 1)
    for a, t in spec.annotations.items():
        if a == "return":
            continue
        doc = args_desc.get(a)
        flags = [f"--{a}"]
        if len(a) == 1 or a[0] not in prefixes:
            flags.insert(0, f"-{a[0]}")
            prefixes.add(a[0])

        if t is bool:
            d = defaults.get(a, False)
            parser.add_argument(*flags, default=d, action="store_true", help=doc)
            # The --no flags are hidden
            parser.add_argument(
                f"--no-{a}", dest=a, action="store_false", help=argparse.SUPPRESS
            )
            continue

        if _is_option_type(t):
            if a not in defaults:
                defaults[a] = None

        action = "store"
        if isinstance(t, _GenericAlias) and t.__origin__ is list:
            action = "append"

        parser.add_argument(
            *flags,
            type=_get_parser(t, flags),
            action=action,
            default=defaults.get(a),
            required=a not in defaults,
            help=doc,
        )
    return parser


def override(
    argparser: argparse.ArgumentParser,
    name: str,
    short_name: str = None,
    # action: str = None,
    # nargs: str =None,
    default: Any = None,
    type: Any = None,
    choices: Any = None,
    required: bool = None,
    help: str = None,
    metavar: str = None,
):
    # Notes:
    #   - nargs: TODO
    #   - actions: supporting this will require recreating the action
    #   - dest: Can't be changed afterward since it would result in some fn arg
    #     not being filled.
    #   - const: I don't think we want to change those, they are only use by
    #     boolean flags.
    candidates = [a for a in argparser._actions if f"--{name}" in a.option_strings]
    assert candidates, f"Can't override behavior of unknown argument {name}."
    assert len(candidates) == 1, f"Found several arguments named {name}."
    action = candidates[0]
    if short_name is not None:
        action.option_strings = [short_name, f"--{name}"]
    if default is not None:
        action.default = default
        action.required = False
    if type is not None:
        action.type = type
    if choices is not None:
        # Useful if you don't want to rewrite code to use enum
        action.choices = choices
    if required is not None:
        assert (
            required or default is not None
        ), "Need a default value to make an argument optional."
        if required:
            action.required = required
            action.default = None
    if help is not None:
        action.help = None
    if metavar is not None:
        action.metavar = metavar
