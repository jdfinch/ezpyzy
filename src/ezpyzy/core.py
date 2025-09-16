from __future__ import annotations

from attrs import define
import cattrs
from typing import Type, TypeVar, Any

T = TypeVar("T")

# A simple attrs data class
@define
class User:
    name: str
    age: int

# A friendly function to show the package works
def greet(who: str) -> str:
    return f"Hello, {who}! It's ezpyzy."

# Use cattrs for structured <-> dict conversions
_converter = cattrs.Converter()

def to_dict(obj: Any) -> dict:
    return _converter.unstructure(obj)

def from_dict(tp: Type[T], data: dict) -> T:
    return _converter.structure(data, tp)
