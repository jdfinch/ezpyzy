
from ezpyzy import Timer
import functools as ft
import collections as cs

with Timer('Create cols'):
    cols = dict(
        a=[i for i in range(10**7)],
        b=[i for i in range(10**7)],
        c=[i for i in range(10**7)],
        d=[i for i in range(10**7)],
        e=[i for i in range(10**7)],
        f=[i for i in range(10**7)],
        g=[i for i in range(10**7)],
        h=[i for i in range(10**7)],
        i=[i for i in range(10**7)],
        j=[i for i in range(10**7)],
    )


with Timer('Column iter'):
    for col in cols.values():
        for item in col:
            pass

get = lambda c, i: cols[c][i]

with Timer('Row iter'):
    for a, b, c, d, e, f, g, h, i, j in zip(*cols.values()):
        x = a
        y = b
        z = c
        w = d
        v = e
        u = f
        t = g
        s = h
        r = i
        q = j