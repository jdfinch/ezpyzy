"""
Todo
"""

from __future__ import annotations

import inspect as ins

from ezpyzy.hash import hash
from ezpyzy.pyon import PYONEncoder, PYONDecoder
from ezpyzy.file import File


def cache(folder='.cache', include_inputs=False):
    ...


if __name__ == '__main__':

    class Foo:
        def __init__(self, x:int, y: str):
            self.x = x
            self.y = y

        def bar(self, z):
            print('bar', z, end=', ')
            print('with', self.x, self.y)


    foo = Foo.__new__(Foo)
    print(foo)
    foo.bar(3)
