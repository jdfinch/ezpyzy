
from __future__ import annotations
import typing as T

import copy as cp
import re

from ezpyzy.alphanumeral import alphanumeral


''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')
OtherColumnTableType = T.TypeVar('OtherColumnTableType')

class Column(T.Generic[ColumnCellType, ColumnTableType]):

    def __init__(self, items=None, name=None, _table:ColumnTableType=None):
        self.__attrs__ = ColumnAttrs(self)
        if name is not None:
            self.__name__ = name
        elif isinstance(items, Column):
            self.__name__ = items.__name__
        else:
            self.__name__ = alphanumeral(len(_table()) if _table is not None else 0)
        if _table is None:
            self.__table__ = Table(cols=[self])
        else:
            self.__table__: ColumnTableType = _table
        if items is not None:
            self += items

    def __call__(self):
        return self.__attrs__

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for self_item, other_item in zip(self, other):
            if self_item != other_item:
                return False
        return True

    def __str__(self):
        max_items = 5
        if len(self) > max_items:
            return f"{self.__name__}[{', '.join(repr(x) for x in self[:max_items-2])}, ..., {repr(self[-1])}]"
        else:
            return f"{self.__name__}[{', '.join(repr(x) for x in self)}]"
    __repr__ = __str__

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        return iter(getattr(row, self.__name__) for row in self.__table__.__rows__)

    def __len__(self):
        return len(self.__table__)

    def __getitem__(self, item):
        return getattr(self.__table__[item], self.__name__)

    def __iadd__(self, other):
        """Cat"""
        assert len(self.__table__()) <= 1, \
            f"Concatenating to column {self} forbidden because it belongs to {self.__table__} of multiple columns"


    def __isub__(self, other):
        """Merge (into table)"""

    def __imul__(self, other):
        """Apply"""

    def __itruediv__(self, other):
        """Group"""

    def __ixor__(self, other):
        """Sort"""

    def __iand__(self, other):
        """Inner Join"""

    def __ior__(self, other):
        """Outer Join"""

    def __ilshift__(self, other):
        """Left Join"""

    def __irshift__(self, other):
        """Right Join"""

    def __imatmul__(self, other):
        """Cartesian Product"""


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


''' ============================== Table ============================== '''

class Table:
    def __init__(self, *rows: T.Iterable[T.Self], cols=None, file=None):
        self.__attrs__: TableAttrs[T.Self] = TableAttrs(self, cols)
        self.__rows__: list[T.Self] = list(row for rows_ in rows for row in rows_)
        if isinstance(cols, Table):
            cols = {col.__name__: col for col in cols()}
        elif cols is None:
            cols = {}
        elif not isinstance(cols, dict):
            cols = {col.__name__: col for col in cols}
        cols = {col_name: cp.copy(col) for col_name, col in cols.items()}
        for col in cols.values():
            col.__table__ = self
        self.__dict__.update(cols)
        self.__getitem_hook__ = None
        self.__getitems_hook__ = None
        self.__contains_hook__ = None

    def __call__(self):
        return self.__attrs__

    def __eq__(self, other: Table):
        self_cols = [col.__name__ for col in self()]
        other_cols = [col.__name__ for col in other()]
        if self_cols != other_cols:
            return False
        for self_col, other_col in zip(self_cols, other_cols):
            if self_col != other_col:
                return False
        return True

    def __iter__(self) -> T.Iterator[T.Self]:
        return iter(self.__rows__)

    def __len__(self):
        return len(self.__rows__)

    def __contains__(self, item):
        if isinstance(item, Column):
            return item in self.__dict__.values()
        else:
            return self.__contains_hook__(item)

    def __getitem__(self, item) -> T.Self:
        """Select"""
        if isinstance(item, int):
            return  self.__rows__[item]
        elif isinstance(item, slice):
            return Table(self.__rows__[item], cols=self)
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
                return Table(cols=self)
            elif isinstance(item[0], int):
                return Table((self.__rows__[i] for i in item), cols=self)
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
            return Table(self.__rows__[item], cols=self)
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
        self.__rows__.extend(other)

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

    def __iter__(self) -> T.Iterator[Column[T.Any, TableAttrsType]]:
        return iter(col for col in self.tab.__dict__.values() if isinstance(col, Column))

    def __contains__(self, item: str | Column):
        if isinstance(item, str):
            return item in self.tab.__dict__
        elif isinstance(item, Column):
            return item in self.tab.__dict__.values()
        else:
            return False

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
            fields[field_name] = Column(name=field_name)
    return fields

class Row(Table, metaclass=RowMeta):
    @classmethod
    def s(cls, *rows, file=None) -> T.Self:
        return Table(*rows, cols=cls.__cols__, file=file)


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

