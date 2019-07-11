from .. import fn_argparser


def check(parser, args, expected):
    parsed = parser.parse_args(args)
    assert vars(parsed) == expected


def test_int_flag():
    def f(xx: int, yy: int = 1):
        pass

    parser = fn_argparser(f)
    check(parser, ["--xx", "1"], dict(xx=1, yy=1))
    check(parser, ["--xx", "1", "--yy", "-3"], dict(xx=1, yy=-3))
    check(parser, ["-x", "1", "-y", "-3"], dict(xx=1, yy=-3))


def test_bool_flag():
    def f(xx: bool, yy: bool = True, zz: bool = False):
        pass

    parser = fn_argparser(f)
    check(parser, [], dict(xx=False, yy=True, zz=False))
    check(parser, ["--xx", "--yy"], dict(xx=True, yy=True, zz=False))
    check(parser, ["--xx", "--yy", "--zz"], dict(xx=True, yy=True, zz=True))
    check(parser, ["-x", "-y", "-z"], dict(xx=True, yy=True, zz=True))
    check(parser, ["-x", "--no-y", "-z"], dict(xx=True, yy=False, zz=True))
    check(parser, ["--no-x", "--no-y", "--no-z"], dict(xx=False, yy=False, zz=False))
    check(parser, ["--no-y"], dict(xx=False, yy=False, zz=False))
