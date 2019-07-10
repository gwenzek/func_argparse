"""Say hello or goodbye to the user."""

import func_argparser


def hello(user: str, times: int = None):
    """Say hello.

    Arguments:
        user: name of the user
    """
    print(f"Hello {user}" * (1 if times is None else times))


def bye(user: str, see_you: float = 1.0):
    """Say goodbye."""
    print(f"Goodbye {user}, see you in {see_you:.1f} days")


if __name__ == "__main__":
    func_argparser.run_main()
