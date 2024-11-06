
import dataclasses as dc

import typing as T


R = T.TypeVar('R')

class Table(T.Generic[R]):
    __cols__ = None
    __maps__ = None
    __rowT__ = None

    def __init__(self, *rows: T.Iterable[R], **columns):
        self.rows: list[R] = []
        self.__maps__: dict[str, dict]
        self.__cols__: dict[str, Column[T.Any, R]]
        self.__rowT__: type[R]


E = T.TypeVar('E')
TR = T.TypeVar('TR')

class Column(T.Generic[E, TR]):
    def __init__(self, *items: T.Iterable[E], name: str=None, table: Table[TR] = None):
        if table is None:
            self.table = Table(**{name: items})
        else:
            assert not items
            self.table: Table[TR] = table
            self.name = name



class RowMeta(type):
    __cols__:tuple[str] = ()
    def __new__(mcs, name, bases, attrs):
        bases = tuple(base for base in bases if base is not Table)
        cls = super().__new__(mcs, name, bases, attrs)
        cls = dc.dataclass(cls) # noqa
        cls.__cols__ = tuple(f.name for f in dc.fields(cls))
        return cls

@dc.dataclass
class Row(Table, metaclass=RowMeta):

    @classmethod
    def s(cls, *rows, **cols) -> T.Self:
        table = Table(*rows, **cols)
        table.__rowT__ = cls
        return table