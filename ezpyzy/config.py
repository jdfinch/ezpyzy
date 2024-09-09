
from __future__ import annotations

import dataclasses as dc
from dataclasses import dataclass
import inspect as ins
import functools as ft

from ezpyzy.setter import setters

import typing as T


def config(cls=None, **kwargs):
    if cls is None:
        return ft.partial(config, **kwargs)
    cls = dc.dataclass(cls)
    cls = setters(cls)
    init = getattr(cls, '__init__', lambda self: None)
    init_sig = ins.signature(init)
    def __init__(self, *args, **kwargs):
        self.__default__ = {
            **{p.name: p.default for p in init_sig.parameters.values() if p.default is not p.empty},
            **{f.name: f.default for f in dc.fields(cls) if f.default is not dc.MISSING},
            **{f.name: f.default_factory() for f in dc.fields(cls) if f.default_factory is not dc.MISSING},
        }
        bound = init_sig.bind(self, *args, **kwargs).arguments
        self.__config__ = {k: v for i, (k, v) in enumerate(bound.items()) if i}
        init(self, *args, **kwargs) # noqa
        del self.__config__
        del self.__default__
    cls.__init__ = __init__
    return cls


F = T.TypeVar('F', bound=T.Callable)


def defaults_from_self(method: F) -> F:
    sig = ins.signature(method)
    @ft.wraps(method)
    def wrapper_method(self, *args, **kwargs):
        binding = sig.bind(self, *args, **kwargs)
        arguments = binding.arguments
        from_self = {k: getattr(self, k) for k in sig.parameters if k not in arguments and hasattr(self, k)}
        arguments.update(from_self)
        result = method(*binding.args, **binding.kwargs)
        return result
    return wrapper_method


class Config:
    __config__: dict[str, T.Any]
    __default__: dict[str, T.Any]


if __name__ == '__main__':

    vars().update(dataclass=config)

    @dataclass
    class A(Config):
        x: int
        y: int = 1
        z: list[str] = dc.field(default_factory=list)

        def __post_init__(self):
            print(f'{self.__config__ = }')
            print(f'{self.__default__ = }')

        @defaults_from_self
        def foo(self, x=None, z=None):
            print('Foo!', f'{x = }', f'{z = }')

        def _set_y(self, value):
            return value * 2


    @dataclass
    class B(A):
        z: list[str] = dc.field(default_factory=lambda: [1, 2, 3])

    a = A(1, y=2)
    print(f'{a = }')
    print(f'{vars(a) = }')
    b = B(8)
    print(f'{b = }')

    b.foo(3)
    b.foo(z=[7, 9])







