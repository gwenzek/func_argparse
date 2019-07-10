# func_argparser

Generate a nice command line interface for a list of functions or a module.
Never worry about your Argparser being out of sync with your code.

## Example

In a 'hello.py' file:
```py
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
    func_argparser.main()
```

From CLI:
```
$ python hello.py hello --user gwenzek
Hello gwenzek

$ python hello.py hello --user gwenzek --times 2
Hello gwenzekHello gwenzek

$ python hello.py bye --user gwenzek --see_you 12.345
Goodbye gwenzek, see you in 12.3 days

$ python hello.py hello -u gwenzek -t 1
Hello gwenzek

$ python hello.py --help
usage: hello.py [-h] {hello,bye} ...

Say hello or goodbye to the user.

positional arguments:
  {hello,bye}
    hello      Say hello.
    bye        Say goodbye.

optional arguments:
  -h, --help   show this help message and exit

$ python hello.py hello --help
usage: hello.py hello [-h] -u USER [-t TIMES]

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  name of the user
  -t TIMES, --times TIMES
```
