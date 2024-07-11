
from __future__ import annotations
import typing as T

import copy as cp
import re

''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')
OtherColumnTableType = T.TypeVar('OtherColumnTableType')

class Column(T.Generic[ColumnCellType, ColumnTableType]):

    def __init__(self, name=None, tab:ColumnTableType=None):
        self.__table__: ColumnTableType = tab
        self.__attrs__ = ColumnAttrs(self)
        self.__name__ = name

    def __call__(self):
        return self.__attrs__

    def __str__(self):
        return self.__name__

    def __repr__(self):
        if len(self) > 4:
            return f"Col({', '.join(repr(x) for x in self[:2])}, ..., {repr(self[-1])})"
        else:
            return f"Col({', '.join(repr(x) for x in self)})"

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        return iter(getattr(row, self.__name__) for row in self.__table__.__rows__)

    def __len__(self):
        return len(self.__table__)

    def __getitem__(self, item):
        return getattr(self.__table__[item], self.__name__)

    def __sub__(
        self: Column[ColumnCellType, ColumnTableType],
        other: Column[T.Any, OtherColumnTableType]
    ) -> ColumnTableType | OtherColumnTableType:
        ...


ColumnAttrsType = T.TypeVar('ColumnAttrsType', bound=Column)

class ColumnAttrs(T.Generic[ColumnAttrsType]):
    def __init__(self, col: ColumnAttrsType):
        self.col: ColumnAttrsType = col

    @property
    def table(self):
        return self.col.__table__


''' ============================== Table ============================== '''

class Table:
    def __init__(self, *rows: T.Iterable[T.Self], cols=None, file=None):
        self.__attrs__ = TableAttrs[T.Self](self, cols)
        self.__rows__: list[T.Self] = list(row for rows_ in rows for row in rows_)
        self.__getitem_hook__ = None
        self.__getitems_hook__ = None
        self.__contains_hook__ = None

    def __call__(self):
        return self.__attrs__

    def __iter__(self) -> T.Iterator[T.Self]:
        return iter(self.__rows__)

    def __len__(self):
        return len(self.__rows__)

    def __contains__(self, item):
        if isinstance(item, Column):
            return item in self.__attrs__.cols.values()
        else:
            return self.__contains_hook__(item)

    def __getitem__(self, item) -> T.Self:
        """Select"""
        if isinstance(item, (int, slice)):
            return Table(self.__rows__[item], cols=self.__attrs__.cols)
        elif isinstance(item, tuple):
            if not item:
                column_view = Table(cols={})
                column_view.__rows__ = self.__rows__
                return column_view
            elif isinstance(item[0], Column):
                column_view = Table(cols={col.__name__: col for col in item})
                column_view.__rows__ = self.__rows__
                return column_view
            else:
                row_selector, *col_selector = item
                rows_view = self[row_selector]
                if not col_selector:
                    return rows_view[col_selector]
                elif isinstance(col_selector[0], Column):
                    column_view = Table(cols={col.__name__: col for col in col_selector})
                    column_view.__rows__ = rows_view.__rows__
                    return column_view
                else:
                    return Table((row[col_selector] for row in rows_view), cols=rows_view.__attrs__.cols)
        elif isinstance(item, list):
            if not item:
                return Table(cols=self.__attrs__.cols)
            elif isinstance(item[0], int):
                return Table((self.__rows__[i] for i in item), cols=self.__attrs__.cols)
            elif isinstance(item[0], bool):
                assert len(item) == len(self.__rows__), f"Boolean selector must be the same length as the table."
                return Table(
                    (row for row, select in zip(self.__rows__, item) if select),
                    cols=self.__attrs__.cols)
            else:
                return Table(self.__getitems_hook__(item), cols=self.__attrs__.cols)
        elif isinstance(item, Column):
            column_view = Table(cols={item.__name__: item})
            column_view.__rows__ = self.__rows__
            return column_view
        elif isinstance(item, ellipsis):
            return Table(self.__rows__, cols=self.__attrs__.cols)
        elif callable(item):
            selector = [item(row) for row in self.__rows__]
            return self[selector]
        else:
            return Table(self.__getitem_hook__(item), cols=self.__attrs__.cols)

    def __setitem__(self, item, value):
        """Insert"""
        if isinstance(item, (int, slice)):
            return Table(self.__rows__[item], cols=self.__attrs__.cols)
        elif isinstance(item, tuple):
            if not item:
                column_view = Table(cols={})
                column_view.__rows__ = self.__rows__
                return column_view
            elif isinstance(item[0], Column):
                column_view = Table(cols={col.__name__: col for col in item})
                column_view.__rows__ = self.__rows__
                return column_view
            else:
                row_selector, *col_selector = item
                rows_view = self[row_selector]
                if not col_selector:
                    return rows_view
                elif isinstance(col_selector[0], Column):
                    column_view = Table(cols={col.__name__: col for col in col_selector})
                    column_view.__rows__ = rows_view.__rows__
                    return column_view
                else:
                    return Table((row[col_selector] for row in rows_view), cols=rows_view.__attrs__.cols)
        elif isinstance(item, list):
            if not item:
                return Table(cols=self.__attrs__.cols)
            elif isinstance(item[0], int):
                return Table((self.__rows__[i] for i in item), cols=self.__attrs__.cols)
            elif isinstance(item[0], bool):
                assert len(item) == len(self.__rows__), f"Boolean selector must be the same length as the table."
                return Table(
                    (row for row, select in zip(self.__rows__, item) if select),
                    cols=self.__attrs__.cols
                )
            else:
                return Table(self.__getitems_hook__(item), cols=self.__attrs__.cols)
        elif isinstance(item, Column):
            column_view = Table(cols={item.__name__: item})
            column_view.__rows__ = self.__rows__
            return column_view
        elif isinstance(item, ellipsis):
            return Table(self.__rows__, cols=self.__attrs__.cols)
        elif callable(item):
            selector = [item(row) for row in self.__rows__]
            return self[selector]
        else:
            return Table(self.__getitem_hook__(item), cols=self.__attrs__.cols)

    def __delitem__(self, item):
        """Clear"""

    def __iadd__(self, other):
        """Cat"""

    def __isub__(self, other):
        """Merge"""

    def __itruediv__(self, other):
        """Group"""

    def __imul__(self, other):
        """Apply"""

    def __ixor__(self, other):
        """Sort"""

    def __imatmul__(self, other):
        """Cartesian product"""

    def __iand__(self, other):
        """Inner join"""

    def __ior__(self, other):
        """Outer join"""

    def __ilshift__(self, other):
        """Left join"""

    def __irshift__(self, other):
        """Right join"""


TableAttrsType  = T.TypeVar('TableAttrsType')

class TableAttrs(T.Generic[TableAttrsType]):
    def __init__(self, tab: TableAttrsType, cols=None):
        self.tab: TableAttrsType = tab
        self.cols: dict[str, Column[T.Any, TableAttrsType]] = {
            col_name: cp.copy(col) for col_name, col in cols.items()
        } if cols else {}
        for col in self.cols.values():
            col.__table__ = self.tab

    def __iter__(self) -> T.Iterator[Column[T.Any, TableAttrsType]]:
        return iter(self.cols.values())

    def __contains__(self, item: str | Column):
        if isinstance(item, str):
            return item in self.cols
        else:
            return item in self.cols.values()

    def save(self):
        ...


''' ============================== Row ============================== '''

CellType = T.TypeVar('CellType')
RowType = T.TypeVar('RowType')
Col = T.Union[Column[CellType, RowType], CellType, None]

class RowMeta(type):
    __cols__ = {}
    def __new__(mcs, name, bases, attrs):
        bases = tuple(base for base in bases if base is not Table)
        cls = super().__new__(mcs, name, bases, attrs)
        cls.__cols__ = inspect_row_layout(cls)
        return cls

col_type_parser = re.compile(r'Col\[([^,]*)')

def inspect_row_layout(cls) -> dict[str, Column]:
    fields = {}
    for field_name, field_type in getattr(cls, '__annotations__', {}).items():
        field_type_str = col_type_parser.findall(str(field_type))
        if field_type_str:
            fields[field_name] = Column(field_name)
            break
    return fields

class Row(Table, metaclass=RowMeta):
    @classmethod
    def s(cls) -> T.Self:
        return Table(cols=cls.__cols__)


''' ============================== Usage ============================== '''
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
            ...

        the_duck = Duck('Donald', 5, ['Huey', 'Dewey', 'Louie'])
        x = the_duck[3:3]

        a_duck = ducks[2]

        some_ducks = ducks.__getitem__(slice(1, 4))
        duck_attrs = ducks[:,3]
        more_ducks = ducks[:,:]
        specific_ducks = ducks[all, 3, 2]
        duck_column = ducks[ducks.name]

        second_col = ducks()[1:2]

        names = ducks.name
        ages = ducks.age
        names_and_ages = names - ages
        names_of_naa = names_and_ages.name


        
    main()

