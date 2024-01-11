
from __future__ import annotations

import typing as T
import functools as ft


def batch(iterable, batch_size=1):
    """Yield batches of size batch_size from iterable."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def batched(fn:T.Callable[[list, ...], list] = None, batch_size=1
    ) -> T.Callable[[list, ...], list]:
    if fn is None:
        return ft.partial(batched, batch_size=batch_size)
    @ft.wraps(fn)
    def batched_fn(ls, *args, **kwargs):
        batches = list(batch(ls, batch_size=batch_size))
        combined = []
        for b in batches:
            batch_result = fn(b, *args, **kwargs)
            combined.extend(batch_result)
        return combined
    return batched_fn