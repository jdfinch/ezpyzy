"""
Instead of:
```py
import typing as T
class Bar(T.Protocol):
    a: int
    b: int

def foo(x: Bar):
    ...
```

Use:
```py
def foo(x):
    x.a; x.b;
    ...
"""


def protocol(*args):
    """
    Does nothing. Use for type annotating attributes without making a Protocol explicitly.
    Pycharm requires parameter attribute accesses to be on the top level of a function for the parameters to get this implicit attribute type annotations.

    :param args: attributes to annotate
    :return: args
    """
    return args



if __name__ == '__main__':

    import dataclasses

    def foo(x=None):
        if x is None:
            x = []
        else:
            x.a; x.b
        return x

    @dataclasses.dataclass
    class Bat:
        a: str

    bat = Bat('2')
    result = foo(bat) # Expected type '{a, b} | None', got 'Bat' instead