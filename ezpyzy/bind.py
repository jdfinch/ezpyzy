
from __future__ import annotations

import functools as ft
import typing as T


F = T.TypeVar('F', bound=T.Callable)

def bind(bound:F) -> F|T.Callable[..., F]:
    return ft.partial(ft.partial, bound)


if __name__ == '__main__':

    def foo(x:int=None, y:float=None) -> float:
        return x + y

    bar = bind(foo)(y=3)
    bat = bar(2)
    print(bat)

