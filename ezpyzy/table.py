
from __future__ import annotations
import typing as T

import copy as cp
import weakref as wr
import re

from ezpyzy.alphanumeral import alphanumeral
from ezpyzy.hash import hash

"""
Primitives:

add column:     Table.__isub__          table -= column/table   ✓
add row:        Table.__iadd__          table += row/table
insert data:    Column.__setitem__      col[...] = value(s)     ✓
delete data:    Column.__delete_data__  del table[...] = None   ✓
del column:     Table.__delitem__       del table[column(s)]
del row:        Table.__delitem__       del table[row(s)]

"""

sentinel = object()



''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')
OtherColumnTableType = T.TypeVar('OtherColumnTableType')
OtherTableType = T.TypeVar('OtherTableType', bound='Table')

class Column(T.Generic[ColumnCellType, ColumnTableType]):

    def __init__(self, *items, name='Column'):
        self.__attrs__ = ColumnAttrs(self)
        if items and isinstance(items[0], Column):
            self.__name__ = items[0].__name__
        else:
            self.__name__ = name
        self.__table__: ColumnTableType = None  # noqa
        if items:
            table = Table()
            table -= self
            items = tuple(item for items_ in items for item in items_)
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
        if self.__table__ is None:
            return f"{self.__name__}[...]"
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

    def __setitem__(self, selector, values):
        if isinstance(selector, int):
            indices = (selector,)
            values = (values,)
        elif isinstance(selector, slice):
            indices = tuple(range(*selector.indices(len(self))))
            assert len(indices) == len(values), f"Cannot set {len(values)} values to {len(indices)} indices selected by {selector} in Column {self} of Table {self.__table__}"
        elif callable(selector):
            selector = tuple(selector(e) for e in self)
            self[selector] = values
            return
        else:
            if not isinstance(selector, (list, tuple)):
                selector = tuple(selector)
            if selector:
                first = selector[0]
                if isinstance(first, bool):
                    assert len(self) == len(selector), f"Boolean selector of length {len(selector)} does not match length {len(self)} of Table {self.__table__}"
                    if len(values) == len(self):
                        indices, values = zip(*((i, v) for i, v in enumerate(values) if selector[i]))
                    else:
                        indices = tuple(i for i, flag in enumerate(selector) if flag)
                        assert len(indices) == len(values), f"Cannot set {len(values)} values to {len(indices)} indices selected by True in boolean selector for Column {self} of Table {self.__table__}"
                elif isinstance(first, int):
                    indices = selector
                    assert len(indices) == len(values), f"Cannot set {len(values)} values to {len(indices)} indices selected by {selector} in Column {self} of Table {self.__table__}"
                else:
                    raise NotImplemented("Custom selectors are not yet implemented")
            else:
                indices = ()
        if self.__insert_data__:
            return self.__insert_data__(indices, values)  # noqa
        else:
            return

    def __insert_data__(self, indices: tuple[int, ...], values: tuple) -> list[int]|None:
        rows = self.__table__.__rows__
        var = self.__name__
        for index, value in zip(indices, values):
            rows[index].__dict__[var] = value
        return None

    __delete_data__: T.Callable[[tuple[int, ...]], list[int]|None] = None

    __add_data__: T.Callable[[tuple[int, ...]], list[int]|None] = None

    def __iadd__(self, other):
        """Cat"""
        assert len(self.__table__()) <= 1, \
            f"Concatenating to column {self} is forbidden because it belongs to {self.__table__} of multiple columns"
        self.__table__ += {self.__name__: other}
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
    def __init__(self, *rows: T.Iterable[T.Self], __layout__:type[Row]=None, __rowtype__=None, **cols):
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
            self.__rowtype__: type[Row] = __layout__
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
        self -= cols
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
            return item is self.__dict__.get(item.__name__)
        elif isinstance(item, Row):
            return item in self.__rows__
        else:
            return self.__contains_hook__(item)

    def __getattr__(self, item):
        column = Column(name=item)
        self -= column
        return column

    def __setattr__(self, key, value):
        if isinstance(value, Column):
            if key != value.__name__:
                if value.__table__ is None:
                    value.__name__ = key
                else:
                    value = type(value)(name=key)
            self -= value
        else:
            super().__setattr__(key, value)

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
                assert len(item) == len(self.__rows__), f"Boolean selector must be the same length as Table {self}, got length {len(item)}"
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

    def __delitem__(self, item):
        """Clear"""

    def __iadd__(self, other):
        """Cat"""
        if isinstance(other, Row):
            self.__rows__.append(other)
            for column in self():
                if column.__add_data__:
                    column.__add_data__((other,))
        else:
            if not isinstance(other, (tuple, list, Table)):
                other = tuple(other)
            if not other:
                return self
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
        if isinstance(other, Column):
            name = other.__name__
            if other.__table__ is None:
                other.__table__ = self
                self.__dict__[name] = other
                other.__add_data__(tuple(range(len(self))))
            else:
                assert len(self) == len(other), f"Cannot merge column {other} with table {self} of different lengths"
                column = type(other)(name=name)
                column.__table__ = self
                self.__dict__[name] = column
                column[tuple(range(len(self)))] = other
        elif isinstance(other, Table):
            assert len(self) == len(other), f"Cannot merge table {other} with table {self} of different lengths"
            for col in other():
                name = col.__name__
                column = type(col)(name=name)
                column.__table__ = self
                self.__dict__[name] = column
                column[tuple(range(len(self)))] = col
        elif isinstance(other, dict):
            other = {name: tuple(col) if not isinstance(col, (tuple, list, Column)) else col
                for name, col in other.items()}
            for name, col in other.items():
                if isinstance(col, Column):
                    if col.__table__ is None:
                        column = col
                        column.__name__ = name
                        column.__table__ = self
                        self.__dict__[name] = column
                        col.__add_data__(tuple(range(len(self))))
                    else:
                        assert len(self) == len(col), f"Cannot merge column {col} with table {self} of unequal length"
                        column = type(col)(name=name)
                        column.__table__ = self
                        self.__dict__[name] = column
                        column[tuple(range(len(self)))] = col
                else:
                    column = Column(name=name)
                    column.__table__ = self
                    self.__dict__[name] = column
                    column[tuple(range(len(self)))] = col
        else:
            for col in other:
                if isinstance(col, Column):
                    if col.__table__ is None:
                        column = col
                        name = alphanumeral(len(self()))
                        column.__table__ = self
                        column.__name__ = name
                        self.__dict__[name] = column
                        col.__add_data__(tuple(range(len(self))))
                    else:
                        assert len(self) == len(col), f"Cannot merge column {col} with table {self} of unequal length"
                        name = col.__name__
                        column = type(col)(name=name)
                        column.__table__ = self
                        self.__dict__[name] = column
                        column[tuple(range(len(self)))] = col
                else:
                    name = alphanumeral(len(self()))
                    column = Column(name=name)
                    column.__table__ = self
                    self.__dict__[name] = column
                    column[tuple(range(len(self)))] = col
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

    def __getattr__(self, item):
        setattr(self.__class__, item, None)
        return None


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

