
from ezpyzy.timer import Timer
import dataclasses as dc
from typing import NamedTuple

class NamedTupleRow(NamedTuple):
    name: str
    age: int
    height: float

@dc.dataclass
class DataClassRow:
    name: str
    age: int
    height: float


with Timer('Creating tuples'):
    x = [(f"Name {i}", i, i * 0.1) for i in range(10**7)]
with Timer('Iterating tuples'):
    for name, age, height in x:
        pass
item = x[0]
with Timer('Accessing tuples'):
    for i in range(10**7):
        age = item[1]

with Timer('Creating lists'):
    y = [[f"Name {i}", i, i * 0.1] for i in range(10**7)]
with Timer('Iterating lists'):
    for name, age, height in y:
        pass
item = y[0]
with Timer('Accessing lists'):
    for i in range(10**7):
        age = item[1]

with Timer('Creating Rows'):
    z = [NamedTupleRow(f"Name {i}", i, i * 0.1) for i in range(10 ** 7)]
with Timer('Iterating Rows'):
    for name, age, height in z:
        pass
item = z[0]
with Timer('Accessing Rows'):
    for i in range(10**7):
        age = item.age

with Timer('Creating DataClasses'):
    w = [DataClassRow(f"Name {i}", i, i * 0.1) for i in range(10 ** 7)]
with Timer('Iterating DataClasses'):
    for row in w:
        pass
item = w[0]
with Timer('Accessing DataClasses'):
    for i in range(10**7):
        age = item.age