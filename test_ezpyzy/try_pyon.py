from __future__ import annotations

from ezpyzy.format import PYON
import dataclasses as dc

@dc.dataclass
class Foo(PYON):
    x: int
    y: str
    z: Foo = None


def try_pyon():
    foo = Foo(1, 'two', Foo(3, 'four'))
    foo.z.z = foo
    saved = foo.serialize()
    print('\n\n', saved, '\n')
    loaded = Foo.deserialize(saved)
    print(loaded)


if __name__ == '__main__':
    try_pyon()