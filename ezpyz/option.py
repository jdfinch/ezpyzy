"""
Instead of:
```py
bar = None if x is None else foo(x)
```

Use:
```py
bar = option(foo)(x)
```
"""

import functools
import typing as T


F = T.TypeVar('F')

def option(fn:F, *items) -> F:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if any(
            arg is None for arg in args
        ) or any(
            value is None for value in kwargs.values()
        ) or any(
            arg is None for arg in items
        ):
            return None
        return fn(*args, **kwargs)
    return wrapper