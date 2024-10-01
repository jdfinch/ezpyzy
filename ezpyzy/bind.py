from __future__ import annotations

import functools as ft
import inspect as ins
import typing as T


F = T.TypeVar('F', bound=T.Callable)

def _partial(f, *args, **kwargs):
    for i, arg in enumerate(args):
        if arg is ...:
            split = i
            break
    else:
        split = None
    if split is not None:
        params = ins.signature(f).parameters
        additional_kwargs = {param.name: arg
            for param, arg in list(zip(params.values(), args))[split+1:]}
        kwargs = {p: a
            for p, a in {**kwargs, **additional_kwargs}.items()
            if a is not ...}
        args = args[:split]
    return ft.partial(f, *args, **kwargs)

def bind(bound:F) -> F|T.Callable[..., F]:
    return ft.partial(_partial, bound)


if __name__ == '__main__':

    def foo(x:int, y:float) -> float:
        return x / y

    bar = bind(foo)(..., 2)
    bat = bar(3)
    print(bat)