
from __future__ import annotations

import typing as T
import functools as ft
import itertools as it


def batching(iterable: T.Iterable | T.Sized, size=None, number=None):
    """Yield batches of speicifed size from iterable."""
    if number:
        if number == -1:
            number = len(iterable)
        size = len(iterable) // number + int(bool(len(iterable) % number))
    elif size == -1:
        size == len(iterable)
    iterator = iter(iterable)
    yield from it.takewhile(bool, (tuple(it.islice(iterator, size)) for _ in it.count()))


def batched(iterable: T.Iterable | T.Sized, size=None, number=None):
    """Return batches of specified size from iterable."""
    if (size, number) == (None, None):
        number = 1
    if number:
        if number == -1:
            number = len(iterable)
        size = len(iterable) // number + int(bool(len(iterable) % number))
    elif size == -1:
        size == len(iterable)
    if hasattr(iterable, '__getitem__') and hasattr(iterable, '__len__'):
        return [iterable[i:i+size] for i in range(0, len(iterable), size)]
    else:
        iterator = iter(iterable)
        return list(it.takewhile(bool, (tuple(it.islice(iterator, size)) for _ in it.count())))



if __name__ == '__main__':

    from ezpyzy import Timer
    import multiprocessing as mp
    from ezpyzy.cat import cat
    import inspect as ins
    from uuid import uuid4
    import sys

    def main():

        with Timer('Create data'):
            data = [[*range(10**1)] for n in range(10**7)]

        with Timer('Batch multiprocessing'):

            processses = 4 # mp.cpu_count()//2

            def parallelize(fn, size=None, number=None):
                data = tuple(ins.signature(fn).parameters.values())[0].default
                def global_fn(*args, **kwargs):
                    return fn(*args, **kwargs)
                global_fn.__name__ = global_fn.__qualname__ = uuid4().hex
                setattr(sys.modules[global_fn.__module__], global_fn.__name__, global_fn)
                batches = batched(data, size=size, number=number)
                with mp.Pool(processes=processses) as pool:
                    results = list(pool.imap(global_fn, batches))
                results = tuple(it.chain(*results))
                return results


            def batch_sum(batch=data):
                return [int(', '.join([str(x) for x in item]).replace(', ', '')[:100]) for item in batch]

            results = parallelize(batch_sum, number=processses)

            print(sum(results))


        with Timer('Single process'):

            results = batch_sum(data)

            print(sum(results))

    main()







