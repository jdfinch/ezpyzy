"""
Utilities for maintaining a type-hinted collection of attributes with easy attribute value swapping.
Two utilities are provided:

`settings` decorates a method to automatically fill parameters with self attributes of the same name, but ONLY when arguments are NOT passsed to those parameters.

`replace` is an in-place (mutating) version of dataclasses.replace, and can be used as a context manager to undo the mutations (puts back the attributes entered with) upon exiting the context.
"""

from __future__ import annotations

import dataclasses
from dataclasses import replace
from dataclasses import dataclass as settings
import functools
import inspect
import contextlib
import sys
import typing as T

F1 = T.TypeVar('F1')
def update_settings(fn:F1) -> F1:
    signature = inspect.signature(fn)
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        binding = signature.bind(*args, **kwargs)
        settings = binding.arguments
        assert 'settings' not in settings, f"settings is a reserved parameter name for {fn.__name__}"
        return fn(*args, settings=settings, **kwargs)
    return wrapper


@contextlib.contextmanager
def temporary_update(obj, originals):
    yield
    obj.__dict__.update(originals)


def replace_inplace(obj, **kwargs):
    objvars = vars(obj)
    kwargs = {k: v for k, v in kwargs.items() if k in objvars}
    vars(obj).update(kwargs)
    if hasattr(obj, '__post_init__'):
        obj.__post_init__()
    context_manager = temporary_update(obj, objvars)
    return context_manager


vars().update(replace=replace_inplace)
'''Magical swap to retain dataclasses.replace type hinting on ez.replace'''


def undefault(__default__=None, __settings__:dict = None, /, **settings):
    if __settings__ is not None:
        settings = {**__settings__, **settings}
    return {k: v for k, v in settings.items() if v is not __default__}


F2 = T.TypeVar('F2')
def specified(fn: F2) -> F2:
    """
    Decorator capturing all arguments passed to the function into a parameter named 'specified' (or into an attribute named 'settings' of the first argument if the function is a method).
    """
    sig = inspect.signature(fn)
    if 'settings' in sig.parameters:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            specified = sig.bind(*args, **kwargs).arguments
            return fn(*args, settings=specified, **kwargs)
    else:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            specified = sig.bind(*args, **kwargs).arguments
            self_param = next(iter(specified))
            self_arg = specified[self_param]
            del specified[self_param]
            self_arg.settings = specified
            return fn(*args, **kwargs)
    return wrapper


C1 = T.TypeVar('C1')

def __settings__(cls: C1) -> C1:
    cls = dataclasses.dataclass(cls)
    cls.__init__ = specified(cls.__init__) # noqa
    return cls

vars().update(settings=__settings__)


class Settings:
    settings = {}


if __name__ == '__main__':

    @settings
    class Foo:
        a: int = 0
        b: int = 1
        c: int = 2
        d: str = 'three'

    foo = Foo(b=4, c=5)
    print(foo)
    print(getattr(foo, 'specified'))

