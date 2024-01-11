"""
Problem: properly type annotate an argument with all of its options, but also cast those options into a single type.
"""

from __future__ import annotations

import functools
import inspect
import types
import typing as T



F = T.TypeVar('F')

def argcast(fn: F=None, **params_included_or_excluded) -> F:
    """
    Decorator for automatically casting arguments of a function to a specified type.

    By default, the type annotation (or first type of a type union) will be used to cast each argument.

    :param fn: function to decorate
    :param params_included_or_excluded: dict of parameters to include or exclude from casting (or a callable to cast with)
    """
    if fn is None:
        return lambda fn: argcast(fn, **params_included_or_excluded)
    signature = inspect.signature(fn)
    if not params_included_or_excluded or any(params_included_or_excluded.values()):
        castable = {
            k: p if not callable(params_included_or_excluded.get(k, None)) else params_included_or_excluded[k]
            for k, p in signature.parameters.items()
            if params_included_or_excluded.get(k, True) is True
            and p.annotation is not inspect.Parameter.empty
            or callable(params_included_or_excluded.get(k, None))
        }
    else:
        castable = {
            k: p
            for k, p in signature.parameters.items()
            if params_included_or_excluded.get(k, False) and p.annotation is not inspect.Parameter.empty
        }
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        for k, v in bound.arguments.items():
            if k in castable:
                if isinstance(castable[k], inspect.Parameter):
                    p = castable[k]
                    cast = (
                        p.annotation.__args__[0]
                        if isinstance(p.annotation, (types.UnionType, T._UnionGenericAlias)) # noqa
                        else p.annotation
                    )
                    kind = p.kind
                else:
                    cast = castable[k]
                    kind = None
                if isinstance(cast, T.ForwardRef):
                    module = inspect.getmodule(fn)
                    cast = getattr(module, cast.__forward_arg__)
                if kind == inspect.Parameter.VAR_POSITIONAL:
                    casted = [cast(x) for x in v]
                elif kind == inspect.Parameter.VAR_KEYWORD:
                    casted = {k: cast(v) for k, v in v.items()}
                else:
                    casted = cast(v)
                bound.arguments[k] = casted
        return fn(*bound.args, **bound.kwargs)
    return wrapper








if __name__ == '__main__':

    ta: T.TypeAlias = T.Union['Bar', set, frozenset, dict]
    tb = T.Union[set, dict]


    @argcast(y=frozenset)
    def foo(x: T.Union['Bar', list, dict], y: set|list):
        print(x)
        print(y)

    class Bar:
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return f'Bar({self.value})'

    foo({1: 'one', 2: 'two'}, [2, 3])