
from __future__ import annotations
import typing as T

import copy as cp
import re

from ezpyzy.alphanumeral import alphanumeral
from ezpyzy.hash import hash


''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')
OtherColumnTableType = T.TypeVar('OtherColumnTableType')
OtherTableType = T.TypeVar('OtherTableType', bound='Table')

class Column(T.Generic[ColumnCellType, ColumnTableType]):

    def __init__(self, *items, name=None, _table:ColumnTableType=None):
        self.__attrs__ = ColumnAttrs(self)
        if name is not None:
            self.__name__ = name
        elif items and isinstance(items[0], Column):
            self.__name__ = items[0].__name__
        else:
            self.__name__ = alphanumeral(len(_table()) if _table is not None else 0)
        if _table is None:
            self.__table__ = Table()
            setattr(self.__table__, self.__name__, self)
        else:
            self.__table__: ColumnTableType = _table
        for item in items:
            self += item

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
            f"Concatenating to column {self} is forbidden because it belongs to {self.__table__} of multiple columns"
        elements = [Row() for _ in range(len(other))]
        for row, element in zip(elements, other):
            setattr(row, self.__name__, element)
        self.__table__ += elements
        return self

    def __imul__(self, other):
        """Apply"""
        return self

    def __itruediv__(self, other):
        """Group"""
        return self

    def __ixor__(self, other):
        """Sort"""
        return self

    def __iand__(self, other):
        """Inner Join"""
        return self

    def __ior__(self, other):
        """Outer Join"""
        return self

    def __ilshift__(self, other):
        """Left Join"""
        return self

    def __irshift__(self, other):
        """Right Join"""
        return self

    def __imatmul__(self, other):
        """Cartesian Product"""
        return self


    def __sub__(self,
        other: Column[OtherColumnTableType]|OtherTableType
    ) -> ColumnTableType | OtherColumnTableType | OtherTableType:
        """Merge"""


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
    def __init__(self, *rows: T.Iterable[T.Self], __layout__=None, __rowtype__=None, **cols):
        self.__attrs__: TableAttrs[T.Self] = TableAttrs(self)
        self.__rows__: list[T.Self] = []
        self.__rowtype__: type[Row] = __rowtype__ or Row
        if __layout__ is None:
            if not cols and rows:
                layout = {}
                for table in rows:
                    if isinstance(table, Table):
                        for c in table():
                            layout[c.__name__] = Column(name=c.__name__, _table=self)
            else:
                layout = {name: Column(name=name, _table=self) for name in cols}
        elif isinstance(__layout__, Table):
            layout = {col.__name__: type(col)(name=col.__name__, _table=self)
                for col in __layout__()}
            self.__rowtype__ = __layout__.__rowtype__
        elif isinstance(__layout__, TableAttrs):
            layout = {col.__name__: type(col)(name=col.__name__, _table=self)
                for col in __layout__}
        elif isinstance(__layout__, type) and hasattr(__layout__, '__cols__'):
            layout = {col.__name__: type(col)(name=col.__name__, _table=self)
                for col in __layout__.__cols__.values()}
            self.__rowtype__ = __layout__
        elif isinstance(__layout__, dict):
            layout = {}
            for name, col in __layout__.items():
                if isinstance(col, Column):
                    layout[name] = type(col)(name=name, _table=self)
                else:
                    layout[name] = Column(name=name, _table=self)
        else:
            layout = {}
            for col in __layout__:
                if isinstance(col, Column):
                    layout[col.__name__] = type(col)(name=col.__name__, _table=self)
                else:
                    layout[col] = Column(name=col, _table=self)
        self.__dict__.update(layout)
        for rows_ in rows:
            self += rows_
        if cols and not rows:
            for name, col in cols.items():
                if col is not None and col is not ...:
                    self.__rows__.extend(Row() for _ in range(len(col))) # noqa ????
                    break
        for name, col in cols.items():
            if col is not None and col is not ...:
                self -= col
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
        elif isinstance(item, Row):
            return item in self.__rows__
        else:
            return self.__contains_hook__(item)

    def __getitem__(self, item) -> T.Self:
        """Select"""
        if isinstance(item, int):
            return  self.__rows__[item]
        elif isinstance(item, slice):
            return Table(self.__rows__[item], __layout__=self)
        elif isinstance(item, tuple):
            if not item:
                column_view = Table(__layout__=(), __rowtype__=self.__rowtype__)
                column_view.__rows__ = self.__rows__
                return column_view
            elif isinstance(item[0], Column):
                cols = tuple(self.__dict__[col.__name__] for col in item)
                column_view = Table(__layout__=cols, __rowtype__=self.__rowtype__)
                column_view.__rows__ = self.__rows__
                return column_view
            else:
                row_selector, *col_selector = item
                if len(col_selector) == 1 and isinstance(col_selector, tuple):
                    col_selector = col_selector[0]
                return self[row_selector][col_selector]
        elif isinstance(item, list):
            if not item:
                return Table(__layout__=self)
            elif isinstance(item[0], Column):
                return self[tuple(item)]
            elif isinstance(item[0], bool):
                assert len(item) == len(self.__rows__), f"Boolean selector must be the same length as the table."
                return Table(
                    (row for row, select in zip(self.__rows__, item) if select), __layout__=self())
            elif isinstance(item[0], int):
                return Table((self.__rows__[i] for i in item), __layout__=self)
            else:
                return Table(self.__getitems_hook__(item), __layout__=self)
        elif isinstance(item, Column):
            col = self.__dict__[item.__name__]
            column_view = Table(__layout__=(col,), __rowtype__=self.__rowtype__)
            column_view.__rows__ = self.__rows__
            return column_view
        elif item == ...:
            return Table(self.__rows__, __layout__=self)
        elif callable(item):
            selector = [item(row) for row in self.__rows__]
            return self[selector]
        else:
            return Table(self.__getitem_hook__(item), __layout__=self)

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
                return Table(__layout__=self())
            elif isinstance(item[0], int):
                return Table((self.__rows__[i] for i in item), __layout__=self())
            elif isinstance(item[0], bool):
                assert len(item) == len(self.__rows__), f"Boolean selector must be the same length as the table."
                return Table(
                    (row for row, select in zip(self.__rows__, item) if select),
                    __layout__=self()
                )
            else:
                return Table(self.__getitems_hook__(item), __layout__=self())
        elif isinstance(item, Column):
            column_view = Table(cols={item.__name__: item})
            column_view.__rows__ = self.__rows__
            return column_view
        elif isinstance(item, ellipsis):
            return Table(self.__rows__, __layout__=self())
        elif callable(item):
            selector = [item(row) for row in self.__rows__]
            return self[selector]
        else:
            return Table(self.__getitem_hook__(item), __layout__=self())

    def __delitem__(self, item):
        """Clear"""

    def __iadd__(self, other):
        """Cat"""
        if not other:
            pass
        else:
            try:
                first = other[0]
            except TypeError:
                other = tuple(other)
                first = other[0]
            if isinstance(first, Row):
                self.__rows__.extend(other)
            elif isinstance(first, dict):
                rows = [self.__rowtype__() for _ in range(len(other))]
                for row, item in zip(rows, other):
                    for var, val in item.items():
                        setattr(row, var, val)
                self.__rows__.extend(rows)
            elif isinstance(first, (list, tuple)):
                rows = [self.__rowtype__() for _ in range(len(other))]
                vars = tuple(col.__name__ for col in self.__attrs__)
                for row, item in zip(rows, other):
                    for var, val in zip(vars, item):
                        setattr(row, var, val)
                self.__rows__.extend(rows)
            else:
                self.__rows__.extend(other)
        return self

    def __isub__(self, other):
        """Merge"""
        return self

    def __itruediv__(self, other):
        """Group"""
        return self

    def __imul__(self, other):
        """Apply"""
        return self

    def __ixor__(self, other):
        """Sort"""
        return self

    def __imatmul__(self, other):
        """Cartesian product"""
        return self

    def __iand__(self, other):
        """Inner join"""
        return self

    def __ior__(self, other):
        """Outer join"""
        return self

    def __ilshift__(self, other):
        """Left join"""
        return self

    def __irshift__(self, other):
        """Right join"""
        return self


TableAttrsType  = T.TypeVar('TableAttrsType')

class TableAttrs(T.Generic[TableAttrsType]):
    def __init__(self, tab: TableAttrsType):
        self.tab: TableAttrsType = tab

    def __iter__(self) -> T.Iterator[Column[T.Any, TableAttrsType]]:
        return iter(col for col in self.tab.__dict__.values() if isinstance(col, Column))

    def __len__(self):
        return len(tuple(col for col in self.tab.__dict__.values() if isinstance(col, Column)))

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
    def s(cls, *rows, **cols) -> T.Self:
        return Table(*rows, __layout__=cls, **cols)


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

