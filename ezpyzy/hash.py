
from __future__ import annotations

import hashlib as hl
import base64 as b64

import ezpyzy.pyr as pyon

serializer = pyon.PyrEncoder()


def hash(o):
    if isinstance(o, str):
        s = o.encode()
    elif isinstance(o, bytes):
        s = o
    else:
        s = serializer.encode(o).encode()
    sha = hl.sha256(s).digest()
    ascii = b64.standard_b64encode(sha).decode('ascii')
    return ascii


if __name__ == '__main__':

    class Foo:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    foo = Foo(2, 39)
    bar = Foo(42, 92)
    bat = Foo(42, 92)

    print(f'{hash(foo) = }')
    print(f'{hash(bar) = }')
    print(f'{hash(bat) = }')
    print(f'{hash(foo) == hash(bar) = }')
    print(f'{hash(bar) == hash(bat) = }')