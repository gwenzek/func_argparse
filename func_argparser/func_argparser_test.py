from . import func_argparser, multi_argparser

from typing import Optional


def check(parser, args, expected):
    parsed = parser.parse_args(args)
    assert vars(parsed) == expected


def test_int_flag():
    def f(xx: int, yy: int = 1):
        pass

    parser = func_argparser(f)
    check(parser, ["--xx", "1"], dict(xx=1, yy=1))
    check(parser, ["--xx", "1", "--yy", "-3"], dict(xx=1, yy=-3))
    check(parser, ["-x", "1", "-y", "-3"], dict(xx=1, yy=-3))


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
