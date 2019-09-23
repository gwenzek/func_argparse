# func_argparse

Generate a nice command line interface for a list of functions or a module.
Never worry about your Argparser being out of sync with your code.
Try it with `pip install func_argparse`.

## Example

In a 'hello.py' file:
```py
"""Say hello or goodbye to the user."""

import func_argparse


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
    func_argparse.main()
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

$ python hello.py bye --help
usage: hello.py bye [-h] -u USER [-s SEE_YOU]

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER
  -s SEE_YOU, --see_you SEE_YOU
                        (default=1.0)
```


## Gotchas

- `func_argparse.main()` create one CLI command by "public" function from a file / module.
- Use `func_argparse.single_main(my_main)` if you only have one entry point in your file.
- All functions arguments need a type hint.
- Arguments without default value will be marked as required.
- A boolean argument `a` will generate two flags: `--a` and `--no-a`.
- A boolean argument with no default value will be assumed to default to `False`.
- The first argument starting with letter `a` will also be available with the flag `-a`.
- The function docstring will be parsed to extract the help messages.
  - First line is used as help message for the function
  - First line starting with `a` will be used to extract the documentation for argument `a`.
    Spaces, dashes and columns will be stripped before displaying.
- Some kind of functions (notably builtin and C-function) can't be inspected and
  we can't generate Argparser for them.
- `func_argparse` generate classics `argparse.Argparser` you can mix and match
  them with hand-written parsers.
- You can't have a function with an argument named `__command` when using `main` or `multi_parser`.
- If you don't like the generated parser, you can modify it using `override` function.
