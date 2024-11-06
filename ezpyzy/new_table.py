from __future__ import annotations
import typing as T

import copy as cp
import weakref as wr
import re

from ezpyzy.alphanumeral import alphanumeral
from ezpyzy.hash import hash


def _imports(): pass


"""
Primitives:

add column:     Table.__isub__          table -= column/table   ✓
add row:        Table.__iadd__          table += row/table      ✓
insert data:    Column.__setitem__      col[...] = value(s)     ✓
delete data:    Column.__delitem__      del col[...]            ✓
del column:     Table.__delitem__       del table[column(s)]    ✓
del row:        Table.__delitem__       del table[row(s)]       ✓              

"""


def _constants(): pass


sentinel = object()
default = object()

''' ============================== Column ============================== '''

"""
1. Creating a floating column from data                                                 => init constructor
2. Creating a floating column about to be attached to a Table (no data, methods throw)  => init constructor
3. Creating a view column for a column-view Table                                       => col view constructor
4. Creating a view column for a row-view Table (also treated as column-view Table)      => row view constructor
5. Creating a column for a Table with a fully defined Row layout (Row.s called)         => model constructor
6. Creating a column to import some data from another Table                             => transfer constructor
"""

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')
OtherColumnTableType = T.TypeVar('OtherColumnTableType')
OtherTableType = T.TypeVar('OtherTableType', bound='Table')


class Column(T.Generic[ColumnCellType, ColumnTableType]):

    def __init__(self, *items, name=default):
        self.__attrs__ = ColumnAttrs(self)
        self.__table__: ColumnTableType = None  # noqa
        if name is default:
            if items and isinstance(items[0], str):
                name, *items = items
            else:
                name = '_'
        self.__name__ = name
        if items:
            table = Table()
            table -= self
            items = tuple(item for items_ in items for item in items_)
            self += items

    def __col_view_init__(self) -> Column[ColumnCellType, ColumnTableType]:
        return cp.copy(self)

    def __row_view_init__(self) -> Column[ColumnCellType, ColumnTableType]:
        return RowViewColumn[ColumnCellType, ColumnTableType](name=self.__name__, original=self)

    def __model_init__(self) -> Column[ColumnCellType, ColumnTableType]:
        return cp.deepcopy(self)

    def __transfer_init__(self) -> Column[ColumnCellType, Table]:
        return Column[ColumnCellType, Table](name=self.__name__)

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
            return f"<Unattached Column object {self.__name__}>"
        max_items = 5
        if len(self) > max_items:
            return f"{self.__name__}[{', '.join(repr(x) for x in self[:max_items - 2])}, ..., {repr(self[-1])}]"
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
        """Insert Data"""
        if isinstance(selector, int):
            indices = (selector,)
            values = (values,)
        elif isinstance(selector, slice):
            indices = tuple(range(*selector.indices(len(self))))
            assert len(indices) == len(
                values
            ), f"Cannot set {len(values)} values to {len(indices)} indices selected by {selector} in Column {self} of Table {self.__table__}"
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
                    assert len(self) == len(
                        selector
                    ), f"Boolean selector of length {len(selector)} does not match length {len(self)} of Table {self.__table__}"
                    if len(values) == len(self):
                        indices, values = zip(*((i, v) for i, v in enumerate(values) if selector[i]))
                    else:
                        indices = tuple(i for i, flag in enumerate(selector) if flag)
                        assert len(indices) == len(
                            values
                        ), f"Cannot set {len(values)} values to {len(indices)} indices selected by True in boolean selector for Column {self} of Table {self.__table__}"
                elif isinstance(first, int):
                    indices = selector
                    assert len(indices) == len(
                        values
                    ), f"Cannot set {len(values)} values to {len(indices)} indices selected by {selector} in Column {self} of Table {self.__table__}"
                else:
                    raise NotImplemented("Custom selectors are not yet implemented")
            else:
                indices = ()
        if self.__insert_data__:
            return self.__insert_data__(indices, values)  # noqa
        else:
            return

    def __insert_data__(self, indices: tuple[int, ...], values: tuple) -> list[int] | None:
        rows = self.__table__.__rows__
        var = self.__name__
        for index, value in zip(indices, values):
            rows[index].__dict__[var] = value
        return None

    def __delitem__(self, selector):
        """Delete Data"""
        if isinstance(selector, int):
            selection = (selector,)
        elif isinstance(selector, slice):
            selection = tuple(range(*selector.indices(len(self))))
        elif callable(selector):
            selection = tuple(selector(value) for value in self)
            return self.__delitem__(selection)
        else:
            if not isinstance(selector, (tuple, list)):
                selector = tuple(selector)
            if not selector:
                return
            first = selector[0]
            if isinstance(first, bool):
                selection = tuple(i for i, flag in enumerate(selector) if flag)
            elif isinstance(first, int):
                selection = selector
            else:
                raise NotImplemented("Custom selectors are not yet implemented")
        if self.__delete_data__:
            return self.__delete_data__(selection)  # noqa

    def __delete_data__(self, selection: tuple[int, ...]) -> list[int] | None:
        """Delete Data"""
        rows = self.__table__.__rows__
        var = self.__name__
        for index in selection:
            del rows[index].__dict__[var]
        return None

    __remove_data__: T.Callable[[tuple[int, ...]], list[int] | None] = None
    """Remove rows from Table"""

    __add_data__: T.Callable[[tuple[int, ...]], list[int] | None] = None
    """Add rows to Table with existing data"""

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

    def __sub__(
        self,
        other: Column[OtherColumnTableType] | OtherTableType
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


RowViewColumnCellType = T.TypeVar('RowViewColumnCellType')
RowViewColumnTableType = T.TypeVar('RowViewColumnTableType')


class RowViewColumn(
    T.Generic[RowViewColumnCellType, RowViewColumnTableType],
    Column[RowViewColumnCellType, RowViewColumnTableType]
):

    def __init__(self, name, original):
        Column.__init__(self, name=name)
        self.__original__ = original

    def __row_view_init__(self) -> Column[ColumnCellType, ColumnTableType]:
        return type(self)(name=self.__name__, original=self.__original__)

    ...  # todo: route primitive mutations to the original Column


''' ============================== Table ============================== '''

"""
0. Create an empty Table without a layout                           ✓
1. Create a Table from some data without a layout                   ✓
2. Create a Table with a Row layout by calling Row.s                
3. Create a Table with column view
4. Create a Table with row view
5. Copy a Table from an existing Table (transfer rows to copy)
"""


class Table:
    def __init__(
        self,
        *rows: T.Iterable[T.Self],
        layout: type[Row] | Table | TableAttrs | dict[str, Column | None] | T.Iterable[Column | str] = None,
        rowtype=None,
        cols: Table | dict[str, Column | T.Iterable] | T.Iterable[Column | T.Iterable] = None
    ):
        self.__attrs__: TableAttrs[T.Self] = TableAttrs(self)
        self.__rows__: list[T.Self] = []
        self.__rowtype__: type[Row] = rowtype or Row
        self.__colnameidx__: int = 0
        if layout is None:
            layout_cols = {}
        elif isinstance(layout, Table):
            layout_cols = {col.__name__: col.__model_init__()
                for col in layout()}
            self.__rowtype__ = layout.__rowtype__
        elif isinstance(layout, TableAttrs):
            layout_cols = {col.__name__: col.__model_init__()
                for col in layout}
        elif isinstance(layout, type) and hasattr(layout, '__cols__'):
            layout_cols = {col.__name__: col.__model_init__()
                for col in layout.__cols__.values()}
            self.__rowtype__: type[Row] = layout  # noqa
        elif isinstance(layout, dict):
            layout_cols = {}
            for name, col in layout.items():
                if isinstance(col, Column):
                    layout_cols[name] = col.__model_init__()
                else:
                    layout_cols[name] = Column(name=name)
        else:
            layout_cols = {}
            for col in layout:
                if isinstance(col, Column):
                    layout_cols[col.__name__] = col.__model_init__()
                else:
                    layout_cols[col] = Column(name=col)
        for name, col in layout_cols.items():
            col.__name__ = self.__getcolname__(name)
            col.__table__ = self
            self.__dict__[col.__name__] = col
        for rows_ in rows:
            self += rows_
        if cols is not None:
            self -= cols

    __flexible__ = False

    def __neg__(self):
        flexible_view = self.__col_view_init__()
        flexible_view.__flexible__ = True
        return flexible_view

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__flexible__ = False

    def __row_view_init__(self):
        # todo: call column row view constructors to copy table
        return ...

    def __col_view_init__(self):
        # todo: call column column view constructors to copy table, and have __rows__ reference the same list in copy
        return ...

    def __getcolname__(self, name="_") -> str:
        # todo: apply this new __getcolname__() to all column-adding places
        if name == "_":
            while isinstance(self.__dict__.get(name := alphanumeral(self.__colnameidx__)), Column):
                self.__colnameidx__ += 1
            self.__colnameidx__ += 1
        else:
            assert name not in self.__dict__
        return name

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

    def __getitem__(self, item) -> T.Self:
        """Select"""
        if isinstance(item, int):
            return self.__rows__[item]
        elif isinstance(item, slice):
            return Table(self.__rows__[item], layout=self)
        elif isinstance(item, tuple):
            if not item:
                column_view = Table(layout=(), rowtype=self.__rowtype__)
                column_view.__rows__ = self.__rows__
                return column_view
            elif isinstance(item[0], Column):
                cols = tuple(self.__dict__[col.__name__] for col in item)
                column_view = Table(layout=cols, rowtype=self.__rowtype__)
                column_view.__rows__ = self.__rows__
                return column_view
            else:
                row_selector, *col_selector = item
                if len(col_selector) == 1 and isinstance(col_selector, tuple):
                    col_selector = col_selector[0]
                return self[row_selector][col_selector]
        elif isinstance(item, list):
            if not item:
                return Table(layout=self)
            elif isinstance(item[0], Column):
                return self[tuple(item)]
            elif isinstance(item[0], bool):
                assert len(item) == len(
                    self.__rows__
                ), f"Boolean selector must be the same length as Table {self}, got length {len(item)}"
                return Table(
                    (row for row, select in zip(self.__rows__, item) if select), layout=self()
                )
            elif isinstance(item[0], int):
                return Table((self.__rows__[i] for i in item), layout=self)
            else:
                return Table(self.__getitems_hook__(item), layout=self)
        elif isinstance(item, Column):
            col = self.__dict__[item.__name__]
            column_view = Table(layout=(col,), rowtype=self.__rowtype__)
            column_view.__rows__ = self.__rows__
            return column_view
        elif item == ...:
            return Table(self.__rows__, layout=self)
        elif callable(item):
            selector = [item(row) for row in self.__rows__]
            return self[selector]
        else:
            return Table(self.__getitem_hook__(item), layout=self)

    def __setitem__(self, item, value):
        """Insert"""

    def __getattr__(self, item):
        column = Column(name=item)
        self -= column
        return column

    def __setattr__(self, key, value):
        if isinstance(value, Column):
            if value.__table__ is not None:
                value = value.__transfer_init__()
            value.__name__ = key
            self -= value
        else:
            super().__setattr__(key, value)

    def __delattr__(self, name):
        """Drop Column"""
        del self[self.__dict__[name]]

    def __delitem__(self, selector):
        """Drop/Delete Data"""
        if isinstance(selector, int):
            for column in self():
                if column.__remove_data__:
                    column.__remove_data__((selector,))
            del self.__rows__[selector]
        elif isinstance(selector, Column):
            selector = self.__dict__[selector.__name__]
            del self.__dict__[selector.__name__]
        elif isinstance(selector, slice):
            selection = tuple(range(*selector.indices(len(self))))
            for column in self():
                if column.__remove_data__:
                    column.__remove_data__(selection)
            del self.__rows__[selector]
        elif callable(selector):
            selection = tuple(selector(row) for row in self.__rows__)
            return self.__delitem__(selection)
        else:
            if not isinstance(selector, (list, tuple)):
                selector = tuple(selector)
            if not selector:
                return
            if isinstance(selector, tuple):
                rselect, *cselect = selector
                if cselect:
                    if isinstance(cselect[0], Column):
                        for column in tuple(self[rselect].__dict__[c.__name__] for c in cselect):
                            del column[:]
                    elif isinstance(cselect[0], slice):
                        for column in list(self[rselect]())[cselect[0]]:
                            del column[:]
                    elif cselect[0] is Ellipsis:
                        for column in self[rselect]():
                            del column[:]
                else:
                    return self.__delitem__(rselect)
            first = selector[0]
            if isinstance(first, bool):
                assert len(self) == len(
                    selector
                ), f"Boolean selector of length {len(selector)} does not match length {len(self)} of Table {self}"
                indices = tuple(i for i, flag in enumerate(selector) if flag)
                for column in self():
                    if column.__remove_data__:
                        column.__remove_data__(indices)
                j = 0
                for i, row in enumerate(self.__rows__):
                    if selector[i]:
                        self.__rows__[j] = row
                        j += 1
                del self.__rows__[j:]
            elif isinstance(first, int):
                for column in self():
                    if column.__remove_data__:
                        column.__remove_data__(selector)
                j = 0
                for i, row in enumerate(self.__rows__):
                    if i in selector:
                        self.__rows__[j] = row
                        j += 1
                del self.__rows__[j:]
            elif isinstance(first, Column):
                for column in tuple(self.__dict__[column.__name__] for column in selector):
                    del self.__dict__[column.__name__]
            else:
                raise NotImplemented("Custom selectors are not yet implemented")

    def __iadd__(self, other):
        """Cat"""
        if isinstance(other, Row):
            self.__rows__.append(other)
            indices = (len(self.__rows__) - 1,)
            for column in self():
                if column.__add_data__:
                    column.__add_data__(indices)
        else:
            if isinstance(other, Table):
                if self.__flexible__:
                    for col in other():
                        if not isinstance(self.__dict__.get(col.__name__), Column):
                            self -= col.__transfer_init__()
            elif not isinstance(other, (tuple, list)):
                other = tuple(other)
            if not other:
                return self
            first = other[0]
            if isinstance(first, Row):
                self.__rows__.extend(rows := other)
            elif isinstance(first, dict):
                if self.__flexible__:
                    col_names = dict.fromkeys(cname for row in other for cname in row)
                    for col_name in col_names:
                        if not isinstance(self.__dict__.get(col_name), Column):
                            self -= Column(name=col_name)
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
                self.__rows__.extend(rows := other)
            indices = tuple(range(len(self), len(self) + len(rows)))
            for column in self():
                if column.__add_data__:
                    column.__add_data__(indices)
        return self

    def __isub__(
        self,
        other: Column | Table | dict[str, Column | T.Iterable] | T.Iterable[Column | T.Iterable]
    ):
        """Merge"""
        if isinstance(other, Column):
            name = self.__getcolname__(other.__name__)
            if other.__table__ is None:
                other.__table__ = self
                other.__name__ = name
                self.__dict__[name] = other
                other.__add_data__(tuple(range(len(self))))
            else:
                assert len(self) == len(other), f"Cannot merge column {other} with table {self} of different lengths"
                column = other.__transfer_init__()
                column.__table__ = self
                column.__name__ = name
                self.__dict__[name] = column
                column[tuple(range(len(self)))] = other
        elif isinstance(other, Table):
            assert len(self) == len(other), f"Cannot merge table {other} with table {self} of different lengths"
            for col in other():
                name = self.__getcolname__(col.__name__)
                column = col.__transfer_init__()
                column.__table__ = self
                column.__name__ = name
                self.__dict__[name] = column
                column[tuple(range(len(self)))] = col
        elif isinstance(other, dict):
            other = {self.__getcolname__(name): tuple(col) if not isinstance(col, (tuple, list, Column)) else col
                for name, col in other.items()}
            for name, col in other.items():
                if isinstance(col, Column):
                    if col.__table__ is None:
                        column = col
                        column.__name__ = name
                        column.__table__ = self
                        self.__dict__[name] = column
                        column.__add_data__(tuple(range(len(self))))
                    else:
                        assert len(self) == len(col), f"Cannot merge column {col} with table {self} of unequal length"
                        column = col.__transfer_init__()
                        column.__table__ = self
                        column.__name__ = name
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
                    name = self.__getcolname__(col.__name__)
                    if col.__table__ is None:
                        column = col
                        column.__table__ = self
                        column.__name__ = name
                        self.__dict__[name] = column
                        column.__add_data__(tuple(range(len(self))))
                    else:
                        assert len(self) == len(col), f"Cannot merge column {col} with table {self} of unequal length"
                        column = col.__transfer_init__()
                        column.__table__ = self
                        self.__dict__[name] = column
                        column[tuple(range(len(self)))] = col
                else:
                    name = self.__getcolname__()
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


TableAttrsType = T.TypeVar('TableAttrsType')


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
        return Table(*rows, layout=cls, **cols)

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
            children.append('Donald')

        the_duck = Duck('Donald', 5, ['Huey', 'Dewey', 'Louie'])
        x = the_duck[3:3]

        a_duck = ducks[2]

        some_ducks = ducks.__getitem__(slice(1, 4))
        duck_attrs = ducks[:, 3]
        more_ducks = ducks[:, :]
        specific_ducks = ducks[all, 3, 2]
        duck_column = ducks[ducks.name]

        certain_ducks = (x := specific_ducks)[x.age, x.children, x.name]

        second_col = ducks()[1:2]

        names = ducks.name().table
        ages = ducks.age
        names_and_ages = names - ages
        names_of_naa = names_and_ages.name


    main()

