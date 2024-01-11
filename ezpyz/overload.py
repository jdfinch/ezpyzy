"""
Works in theory, but the problem is that type checkers don't really support @overload yet.
"""

import functools
import inspect
import typing


class Overload:
    def __init__(self):
        self.overloads = {}
        self.master = None

    def __call__(self, *args, **kwargs):
        which = self.master(*args, **kwargs)
        assert which in self.overloads or id(which) in self.overloads, f'{which} not found in {self.overloads}'
        if which in self.overloads:
            return self.overloads[which](*args, **kwargs)
        else:
            return self.overloads[id(which)](*args, **kwargs)

    def __get__(self, instance, owner):
        return functools.partial(self.__call__, instance or owner)

    def overload(self, fn, key=None):
        if key is None and not callable(fn):
            return functools.partial(self.overload, key=fn)
        self.overloads[id(fn)] = fn
        if hasattr(fn, '__name__'):
            self.overloads[fn.__name__] = fn
        self.overloads[key] = fn
        self.master = fn
        return self


F = typing.TypeVar('F')

def overload(fn: F = None, key=None) -> F:
    if key is None and not callable(fn):
        return functools.partial(overload, key=fn)
    elif fn is None:
        return functools.partial(overload, key=key)
    context = inspect.currentframe().f_back.f_locals
    existing = context.get(fn.__name__)
    if isinstance(existing, Overload):
        return existing.overload(fn, key)
    else:
        return Overload().overload(fn, key)


'''Lol, type checker bamboozled'''
_tmp_overload = typing.overload
setattr(typing, 'overload', overload)
overload = typing.overload
setattr(typing, 'overload', _tmp_overload)








if __name__ == '__main__':

    class Bar:

        @overload
        def foo(self, x: int):
            return x + 1

        @overload
        def foo(self, y: str, z: str = "0"):
            return float(y) + float(z) + 1

        @overload
        def foo(self, x: list[float], c: float = 0):
            return sum(x) + c + 1

        @overload
        def foo(self, x, y):
            if isinstance(x, int):
                return


    bar = Bar()
    print(f'{bar.foo("3") = }')






