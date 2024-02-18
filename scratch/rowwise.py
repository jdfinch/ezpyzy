
from ezpyzy import Timer
import functools as ft
import collections as cs
import dataclasses as dc
import typing as T
import time

@dc.dataclass
class RowTuple:
    # __slots__ = 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int
    h: int
    i: int
    j: int

with Timer('Create rows'):
    rows = [
        RowTuple(i, i, i, i, i, i, i, i, i, i)
        for i in range(10**7)
    ]

# with Timer('Column iter'):
#     for col in zip(*rows):
#         x = len(col)

with Timer('Row iter'):
    for row in rows:
        x = row.a


import gc
time.sleep(10)
with Timer('Delete Column'):
    for row in rows:
        del row.a
gc.collect()
time.sleep(10)