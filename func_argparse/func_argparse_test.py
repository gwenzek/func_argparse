import enum
import io
import pytest
import sys

from typing import List, Optional, Union

from . import func_argparser, multi_argparser, override


def check(parser, args, expected):
    parsed = parser.parse_args(args)
    assert expected == vars(parsed)


def check_fail(parser, args, error):
    err = sys.stderr
    try:
        sys.stderr = io.StringIO()
        with pytest.raises(SystemExit):
            parser.parse_args(args)
        assert error in sys.stderr.getvalue()
    finally:
        sys.stderr = err


def test_int_flag():
    def f(xx: int, yy: int = 1):
        pass

    parser = func_argparser(f)
    check(parser, ["--xx", "1"], dict(xx=1, yy=1))
    check(parser, ["--xx", "1", "--yy", "-3"], dict(xx=1, yy=-3))
    check(parser, ["-x", "1", "-y", "-3"], dict(xx=1, yy=-3))
    check_fail(parser, ["-x", "foo"], "argument -x/--xx: invalid int value: 'foo'")
    check_fail(parser, ["-y", "1"], "the following arguments are required: -x/--xx")


def test_return_type():
    def f(xx: int, yy: int = 1) -> int:
        pass

    parser = func_argparser(f)
    check(parser, ["--xx", "1"], dict(xx=1, yy=1))
    check(parser, ["-x", "1", "-y", "-3"], dict(xx=1, yy=-3))
    check_fail(parser, ["-x", "foo"], "argument -x/--xx: invalid int value: 'foo'")


def test_bool_flag():
    def f(xx: bool, yy: bool = True, zz: bool = False):
        pass

    parser = func_argparser(f)
    check(parser, [], dict(xx=False, yy=True, zz=False))
    check(parser, ["--xx", "--yy"], dict(xx=True, yy=True, zz=False))
    check(parser, ["--xx", "--yy", "--zz"], dict(xx=True, yy=True, zz=True))
    check(parser, ["-x", "-y", "-z"], dict(xx=True, yy=True, zz=True))
    check(parser, ["-x", "--no-y", "-z"], dict(xx=True, yy=False, zz=True))
    check(parser, ["--no-x", "--no-y", "--no-z"], dict(xx=False, yy=False, zz=False))
    check(parser, ["--no-y"], dict(xx=False, yy=False, zz=False))


def test_optional():
    def f(xx: str = None):
        pass

    parser = func_argparser(f)
    check(parser, [], dict(xx=None))
    check(parser, ["--xx", "foo"], dict(xx="foo"))

    def g(xx: Optional[str]):
        pass

    parser = func_argparser(g)
    check(parser, [], dict(xx=None))
    check(parser, ["--xx", "foo"], dict(xx="foo"))


def test_union():
    def f(xx: Union[int, float]):
        pass

    parser = func_argparser(f)
    check(parser, ["--xx", "3"], dict(xx=3))
    check(parser, ["--x", "3.1"], dict(xx=3.1))
    check_fail(
        parser,
        ["-x", "foo"],
        "argument -x/--xx: invalid Union[int, float] value: 'foo'",
    )

    def g(xx: Union[str, int]):
        pass

    parser = func_argparser(g)
    check(parser, ["--xx", "foo"], dict(xx="foo"))
    # Union types are tried in the order they are specified
    check(parser, ["--xx", "3"], dict(xx="3"))

    class Color(enum.Enum):
        RED = 1

    def h(xx: Union[int, Color, str]):
        pass

    parser = func_argparser(h)
    check(parser, ["--xx", "3"], dict(xx=3))
    check(parser, ["--xx", "red"], dict(xx=Color.RED))
    check(parser, ["--xx", "foo"], dict(xx="foo"))


def test_enum():
    class Color(enum.Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    def f(color: Color):
        pass

    parser = func_argparser(f)
    check(parser, ["--color", "RED"], dict(color=Color.RED))
    check(parser, ["-c", "BLUE"], dict(color=Color.BLUE))
    check(parser, ["-c", "blue"], dict(color=Color.BLUE))
    check_fail(parser, ["-c", "xx"], "argument -c/--color: invalid choice: 'xx'")


def test_list():
    def f(xx: List[int]):
        pass

    parser = func_argparser(f)
    check(parser, ["--xx", "1", "--xx", "2", "--xx", "3"], dict(xx=[1, 2, 3]))
    check(parser, ["--xx", "1", "-x", "2", "--xx", "3"], dict(xx=[1, 2, 3]))
    check_fail(parser, [], "the following arguments are required: -x/--xx")

    def g(xx: List[int] = []):
        pass

    parser = func_argparser(g)
    check(parser, ["--xx", "1", "--xx", "2", "--xx", "3"], dict(xx=[1, 2, 3]))
    check(parser, ["--xx", "1", "-x", "2", "--xx", "3"], dict(xx=[1, 2, 3]))
    check(parser, [], dict(xx=[]))


def test_multi():
    def f(xx: int, yy: int = 1):
        pass

    def g(xx: bool, yy: bool = False):
        pass

    def h(xx: Optional[str]):
        pass

    parser = multi_argparser(f, g, h)
    check(parser, ["f", "--xx", "1"], dict(__command=f, xx=1, yy=1))
    check(parser, ["g", "--xx"], dict(__command=g, xx=True, yy=False))
    check(parser, ["h", "--xx", "foo"], dict(__command=h, xx="foo"))


def test_flag_collision():
    def f(xx: int, xxx: int = 1):
        pass

    parser = func_argparser(f)
    check(parser, ["--xx", "1"], dict(xx=1, xxx=1))
    check(parser, ["--xx", "1", "--xxx", "-3"], dict(xx=1, xxx=-3))
    check(parser, ["-x", "3"], dict(xx=3, xxx=1))

    def g(xx: int = 0, x: int = 1):
        pass

    parser = func_argparser(g)
    check(parser, ["--xx", "1"], dict(xx=1, x=1))
    check(parser, ["--xx", "1", "--x", "-3"], dict(xx=1, x=-3))
    check(parser, ["--xx", "1", "-x", "-3"], dict(xx=1, x=-3))
    check(parser, ["--x", "3"], dict(xx=0, x=3))
    check(parser, ["-x", "3"], dict(xx=0, x=3))


def test_help(capsys):
    def f(xx: int, yy: int = 1):
        """Awesome documentation.

        xx should be an int
        yy: the y coordinate
        """
        pass

    func_argparser(f).print_help()
    out = capsys.readouterr().out
    assert "Awesome documentation." in out
    assert "the y coordinate (default=1)" in out


def test_help_bool_flag(capsys):
    def f(xx: bool = False, yy: bool = True):
        """Awesome documentation.

        xx: use some xx
        yy: use some yy
        """
        pass

    func_argparser(f).print_help()
    out = capsys.readouterr().out
    assert "Awesome documentation." in out
    assert "use some xx (default=False)" in out
    assert "use some yy (default=True, --no-yy to disable)" in out


def test_override_required():
    def f(xx: int, yy: int = 1):
        pass

    parser = func_argparser(f)
    check_fail(parser, [], "the following arguments are required: -x/--xx")
    check_fail(parser, ["--yy", "3"], "the following arguments are required: -x/--xx")

    override(parser, "xx", default=2)
    override(parser, "yy", required=True)

    check_fail(parser, [], "the following arguments are required: -y/--yy")
    check(parser, ["--yy", "3"], dict(xx=2, yy=3))


def test_override_type():
    def f(xx: int = 0xFFF):
        pass

    parser = func_argparser(f)
    check_fail(
        parser, ["--xx", "0xF00"], "argument -x/--xx: invalid int value: '0xF00'"
    )

    override(parser, "xx", type=lambda x: int(x, 0))
    check(parser, ["--xx", "0xF00"], dict(xx=0xF00))


def test_override_choice():
    def f(xx: str):
        assert xx in ("foo", "foobar", "bar")

    parser = func_argparser(f)
    check(parser, ["--xx", "bar"], dict(xx="bar"))
    check(parser, ["--xx", "baz"], dict(xx="baz"))

    override(parser, "xx", choices=("foo", "foobar", "bar"))
    check(parser, ["--xx", "bar"], dict(xx="bar"))
    check_fail(
        parser,
        ["--xx", "baz"],
        "invalid choice: 'baz' (choose from 'foo', 'foobar', 'bar')",
    )


def test_class_parser(capsys):
    class Foo:
        """Foo documentation"""

        def __init__(self, xx: int):
            """__init__ documentation"""
            self.xx = xx

    parser = func_argparser(Foo)
    check(parser, ["--xx", "3"], dict(xx=3))

    parser.print_help()
    out = capsys.readouterr().out
    # Prefer __init__ documentation over Foo ones
    assert "__init__" in out
