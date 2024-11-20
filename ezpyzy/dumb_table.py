from __future__ import annotations


import dataclasses as dc
import copy as cp
from ezpyzy.peek import peek

import typing as T


R = T.TypeVar('R', bound='Row')

class Table(T.Generic[R]):
    __cols__ = None
    __row_type__ = None
    __attrs__ = None

    def __init__(self, *rows: T.Iterable[R], **columns):
        self.__rows__: list[R] = []
        self.__cols__: dict[str, Column[T.Any, R]]
        self.__row_type__: type[R]

    def __call__(self) -> 'TableAttrs[T.Self]':
        if self.__attrs__ is None:
            self.__attrs__ = TableAttrs(self)
        return self.__attrs__

    def __iter__(self) -> T.Iterator[R]:
        return self.__rows__.__iter__()

    def __len__(self):
        return len(self.__rows__)

    def __getattr__(self, item):
        if item in self.__cols__:
            column = self.__cols__[item]
            if column is None:
                column = Column(table=self, name=item)
                self.__cols__[item] = column
            return column
        return super().__getattr__(item)

    def __setattr__(self, key, value):
        if isinstance(value, Column):
            if value.__table__ is self and value.__name__ == key:
                return
            assert len(self) == len(value), \
                f"Merged Column must be same length as table {self}. Got {len(value) = } and {len(self) = }"
            self.__cols__[key] = None
            for row, val in zip(self, value):
                setattr(row, key, val)
        else:
            super().__setattr__(key, value)

    def __delattr__(self, item):
        if item in self.__cols__:
            del self.__cols__[item]
            for row in self:
                delattr(row, item)
        else:
            super().__delattr__(item)

    def __getitem__(self, selection) -> R:
        if isinstance(selection, int):
            return self.__rows__.__getitem__(selection)
        elif isinstance(selection, slice):
            return self.__class__(self.__rows__[selection]) # noqa
        elif selection is ellipsis:
            return self.__class__(self.__rows__) # noqa
        elif isinstance(selection, tuple) and selection:
            first = selection[0]
            if isinstance(first, (Column, str)):
                col_view = cp.copy(self)
                if selection[-1] is ellipsis:
                    selected_cols = tuple(c.__name__ if isinstance(c, Column) else c for c in selection[:-1])
                    rest_of_cols = tuple(col for col in self.__cols__ if col not in selected_cols)
                    col_view.__cols__ = dict.fromkeys(selected_cols+rest_of_cols)
                else:
                    col_view.__cols__ = dict.fromkeys(c if isinstance(c, str) else c.__name__ for c in selection)
                col_view.__attrs__ = None
                return col_view # noqa
            if not isinstance(first, (Column, str)):
                col_selection = selection[1:]
                if col_selection and isinstance(col_selection[0], (str, Column)):
                    rows_view = self[first]
                    return rows_view[col_selection]
        elif isinstance(selection, Column):
            ...
        elif isinstance(selection, (Table, TableAttrs)):
            ...
        elif callable(selection):
            selection = [selection(row) for row in self.__rows__]
        if not selection:
            return self.__class__()  # noqa
        if isinstance(selection, set):
            return self.__class__(row for row in self.__rows__ if row in selection) # noqa
        else:
            if (iterator:=iter(selection)) is iter(selection):
                first, selection = peek(selection)
            else:
                first = next(iterator)
            if isinstance(first, bool):
                assert len(selection) == len(self.__rows__), \
                    f'Boolean selection must be same length as table. Got {len(selection) = } and {len(self) = }'
                return self.__class__(row for row, i in zip(self.__rows__, selection) if i) # noqa
            if isinstance(first, int):
                return self.__class__(self.__rows__[i] for i in selection) # noqa
            else:
                assert len(selection) == len(self.__rows__), \
                    f'Boolean selection must be same length as table. Got {len(selection) = } and {len(self) = }'
                return self.__class__(row for row, i in zip(self.__rows__, selection) if i)  # noqa

    def __setitem__(self, selection, data):
        ...

    def __iadd__(self, other) -> R:
        if self.__row_type__ and isinstance(other, self.__row_type__):
            self.__rows__.append(other)
        elif not self.__row_type__:
            self.__rows__.extend(other)
        elif isinstance(other, dict):
            rows = zip(*other.values())
            self.__rows__.extend(self.__row_type__(**dict(zip(other, row))) for row in rows)
        else:
            if (iterator:=iter(other)) is iter(other):
                first, other = peek(other)
            else:
                first = next(iterator)
            if isinstance(first, self.__row_type__):
                self.__rows__.extend(other)
            elif isinstance(first, dict):
                self.__rows__.extend(self.__row_type__(**row) for row in other)
            elif isinstance(first, Column):
                rows = zip(*other)
                cols = (col.__name__ for col in other)
                self.__rows__.extend(self.__row_type__(**dict(zip(cols, row))) for row in rows)
            else:
                self.__rows__.extend(self.__row_type__(**dict(zip(self.__cols__, row))) for row in other)
        return self # noqa




TableAttrsType  = T.TypeVar('TableAttrsType')

class TableAttrs(T.Generic[TableAttrsType]):
    def __init__(self, table: TableAttrsType):
        self.table: TableAttrsType = table

    def __iter__(self):
        return iter(self.table.__cols__.values())

    def __len__(self):
        return len(self.table.__cols__)

    def __getitem__(self, item):
        return self.table.__cols__[item]



E = T.TypeVar('E')
TR = T.TypeVar('TR')

class Column(T.Generic[E, TR]):
    __attrs__ = None
    def __init__(self, *items: T.Iterable[E], name: str=None, table: Table[TR] = None):
        if table is None:
            self.__table__ = Table(**{name: items})
            self.__table__.__cols__[name] = self
        else:
            assert not items
            self.__table__: Table[TR] = table
            self.__name__ = name

    def __call__(self) -> 'ColumnAttrs[T.Self]':
        if self.__attrs__ is None:
            self.__attrs__ = ColumnAttrs(self)
        return self.__attrs__

    def __iter__(self) -> T.Iterator[E]:
        return (getattr(row, self.__name__) for row in self.__table__)

    def __getitem__(self, item) -> E|Column[E, TR]:
        return getattr(self.__table__[item], self.__name__)



ColumnAttrsType = T.TypeVar('ColumnAttrsType', bound=Column)

class ColumnAttrs(T.Generic[ColumnAttrsType]):
    def __init__(self, col: ColumnAttrsType):
        self.col: ColumnAttrsType = col

    @property
    def table(self):
        return self.col.__table__

    @property
    def name(self):
        return self.col.__name__



CellType = T.TypeVar('CellType')
RowType = T.TypeVar('RowType')
Col = T.Union[Column[CellType, RowType], CellType, None]


class RowMeta(type):
    __cols__:tuple[str] = ()
    def __new__(mcs, name, bases, attrs):
        bases = tuple(base for base in bases if base is not Table)
        cls = super().__new__(mcs, name, bases, attrs)
        cls = dc.dataclass(cls) # noqa
        cls.__cols__ = tuple(f.name for f in dc.fields(cls))
        return cls

@dc.dataclass
class Row(Table[T.Self], metaclass=RowMeta):

    @classmethod
    def s(cls, *rows, **cols) -> T.Self:
        table = Table(*rows, **cols)
        table.__row_type__ = cls
        return table

    def __getattr__(self, item):
        setattr(self.__class__, item, None)
        return None


if __name__ == '__main__':

    import dataclasses as dc


    @dc.dataclass
    class Duck(Row):
        name: Col[str, Duck] = None
        age: Col[int, Duck] = None
        children: Col[list[str], Duck] = None

        def quack(self) -> Col[str]:
            return f'{self.name} quack!'


    def main():
        ducks = Duck.s()
        for duck in ducks:
            duck.quack()
        for children in ducks.children:
            children.append('Donald')

        the_duck = Duck('Donald', 5, ['Huey', 'Dewey', 'Louie'])

        a_duck = ducks[2]

        some_ducks = ducks.__getitem__(slice(1, 4))
        duck_attrs = ducks[:]
        more_ducks = ducks[:, :]
        specific_ducks = ducks[all, 3, 2]
        duck_column = ducks[ducks.name]

        certain_ducks = (x := specific_ducks)[x.age, x.children, x.name]

        second_col = ducks()[1:2]

        names = ducks.name
        ages = ducks.age
        names_and_ages = names - ages
        names_of_naa = names_and_ages.name
