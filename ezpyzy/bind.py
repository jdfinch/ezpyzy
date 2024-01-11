
from __future__ import annotations

import functools
import typing as T


F = T.TypeVar('F')

def bind(bound:F) -> F | T.Callable[..., F]:
    @functools.wraps(bound)
    def wrapper(*args, **kwargs):
        arguments = []
        for arg in args:
            if arg is not ...:
                arguments.append(arg)
            else:
                break
        return functools.partial(bound,
            *arguments,
            **{k: v for k, v in kwargs.items() if v is not ...}
        )
    return wrapper


if __name__ == '__main__':

    def foo(x=None, y=None):
        return x + y

    bar = bind(foo)(1, ...)
    print(bar(y=2))

