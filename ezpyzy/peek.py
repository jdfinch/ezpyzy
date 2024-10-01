
from __future__ import annotations

import itertools as it

import typing as T


E = T.TypeVar('E')

def peek(iterable: T.Iterable[E]) -> tuple[E | None, T.Iterable[E]]:
    """
    Get (the first element, iterable without the first element consumed).
    """
    iterating = iter(iterable)
    try:
        e = next(iterating)
        i = it.chain((e,), iterating)
    except StopIteration:
        e = None
        i = iterable
    return e, i

