"""
Utilities for maintaining a type-hinted collection of attributes with easy attribute value swapping.
Two utilities are provided:

`settings` decorates a method to automatically fill parameters with self attributes of the same name, but ONLY when arguments are NOT passsed to those parameters.

`replace` is an in-place (mutating) version of dataclasses.replace, and can be used as a context manager to undo the mutations (puts back the attributes entered with) upon exiting the context.
"""

from __future__ import annotations

from dataclasses import replace
import functools
import inspect
import contextlib
import sys
import typing as T

F1 = T.TypeVar('F1')
def settings(fn:F1) -> F1:
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


sys.modules[__name__].__dict__.update(replace=replace_inplace)


def undefault(__default__=None, __settings__:dict = None, /, **settings):
    if __settings__ is not None:
        settings = {**__settings__, **settings}
    return {k: v for k, v in settings.items() if v is not __default__}



if __name__ == '__main__':
    '''
    import dataclasses

    @dataclasses.dataclass
    class Foo:
        x: int
        y: str
        z: list[str]

        @settings
        def show(self, y=None):
            return f"x={self.x}, y={y}, z={self.z}"


    foo = Foo(1, '3', ['4'])
    print(f'{foo = }')

    replace(foo, x=2)
    print(f'{foo = }')

    with replace(foo, x=9, z=['9']):
        print(f'    {foo = }')
        with replace(foo, y='9'):
            print(f'        {foo = }')
        print(f'    {foo = }')

    print(f'{foo = }')
    print()

    print(f'{foo.show() = }')
    print(f'{foo.show("hello world") = }')
    '''






