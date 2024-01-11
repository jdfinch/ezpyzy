from __future__ import annotations

from ezpyzy import file
import typing as T



class AutocachedFunction:

    def __init__(self, fn, format):
        self.fn = fn
        self.format = format

    def __call__(self, *args, save=None, load=None, **kwargs):
        if load is not None:
            return file.File(load).load()
        result = self.fn(*args, **kwargs)
        if save is not None:
            f = file.File(save, format=self.format)
            f.save(result)
        return result


F = T.TypeVar('F')

def autocache(fn:F=None, *, format=None) -> F | AutocachedFunction:
    if fn is None:
        return lambda fn: autocache(fn, format=format)
    return AutocachedFunction(fn, format=format)




