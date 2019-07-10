# func_argparser

Generate a nice command line interface for a list of functions or a module.

## Example

In a 'hello.py' file:
```py
import func_argparser

def hello(user: str, times: int = None):
    print(f"Hello {user}" * (1 if times is None else times))

def bye(user: str, see_you: float = 1.0):
    print(f"Goodbye {user}, see you in {see_you:.1f} days"


if __name__ == "__main__":
    func_argparser.run_main()
```

From CLI:
```sh
> python hello.py hello --user gwenzek
Hello gwenzek
> python hello.py hello --user gwenzek --times 2
Hello gwenzekHello gwenzek
> python hello.py bye --user gwenzek --see_you 12.345
Goodbye gwenzek, see you in 12.3 days
> python hello.py hello -u gwenzek -t 1
Hello gwenzek
```
