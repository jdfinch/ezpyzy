
from __future__ import annotations
import typing as T
import os
import math
import multiprocessing as mp
import functools as ft
from ezpyzy.captured_vars import CapturedVars


F = T.TypeVar('F')

class MultiprocessedFunctionApplyContext(T.Generic[F]):
    def __init__(self, fn: F, processes=-1, batchsize=None):
        self.fn = fn
        self.processes = os.cpu_count() if processes == -1 else processes
        self.batchsize = batchsize
        self.captured = None
        self.pool = None

    def __call__(self, *args, **kwargs):
        assert self.pool is not None, \
            f"Function {self.fn} applied with ez.apply was called without entering a multiprocessing context. " \
            f"To create the apply context, use a with block like:\n    with apply({self.fn.__name__}) as f: ..."
        return ft.partial(self.fn, *args, **kwargs)

    def __enter__(self) -> F:
        self.captured = CapturedVars(2).__enter__()
        self.pool = mp.Pool(processes=self.processes).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.captured.__exit__(exc_type, exc_val, exc_tb)
        for var, val in self.captured:
            if val is self: continue
            results = self.pool.map(call, val, chunksize=self.batchsize)
            setattr(self.captured, var, list(results))
        self.pool.__exit__(exc_type, exc_val, exc_tb)
        self.pool = None
        self.captured = None

def call(f):
    return f()


def apply(fn: F, processes=-1, batchsize=None) -> MultiprocessedFunctionApplyContext[F]:
    return MultiprocessedFunctionApplyContext(fn, processes=processes, batchsize=batchsize)




if __name__ == '__main__':

    import random as rng
    from ezpyzy.timer import Timer

    with Timer('Creating data'):
        row = [rng.randint(0, h) for h in range(10**2)]
        data = [list(row) for _ in range(10**6)]


    def foo(x: str, y: list[int]) -> str:
        return '/'.join(f"{x}: {y}".lower().split())[:100]

    for ll in range(2, 8):
        with Timer(f'With {ll} processes'):
            with apply(foo, processes=ll, batchsize=None) as summify:
                sums = [summify('Random numbers', row) for row in data]
        print(sums[273])

    with Timer('Single process'):
        sums = [foo('Random numbers', row) for row in data]
    print(sums[273])


    for ll in range(2, 8):
        with Timer(f'Traditional multiprocessing with {ll} processes'):
            with mp.Pool(processes=ll) as pool:
                sums = pool.starmap(foo, [('Random numbers', row) for row in data])
        print(sums[273])


    '''
    Problem: Gaining performance from parallelism is fundamentally a divide-and-conquer problem.
             However, if the majority of work is done element-by-element such as calling functions
             or collating elements to send to worker processes, the performance gain disappears.
             
             This happens in the above example because the amount of apply work per element is low.
             
             A better way is to just batch the list of data ahead of time and send each batch to
             a different worker process. This way, within each batch, there is no overhead, so a
             small amount of work per element doesn't matter.
    '''