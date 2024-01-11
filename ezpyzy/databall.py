"""
This is a bad way to solve the problem of "snowballing" attributes.

The idea is that an object is created with some attributes, and more are added throughout a pipeline or process.

The better solution is to use a column-based table structure, where additional columns can be easily added without
invalidating the underlying structure of data and methods. See table.py.
"""

from dataclasses import dataclass


@dataclass
class Foo:
    a: int = None
    b: str = None
    c: list[float] = None

@dataclass
class Bar(Foo):
    d: set[str] = None
    e: dict[str, str] = None

@dataclass
class Bat(Bar):
    g: str = None


ball = Bat(1, '2', [3], {'4'}, {'5': '6'}, '7')
print(ball)