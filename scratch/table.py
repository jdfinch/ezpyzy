from __future__ import annotations
import dataclasses as dc
import weakref as wr
from dataclasses import dataclass
import copy
import typing as T



ElementType = T.TypeVar('ElementType')

class Column(T.Generic[ElementType]):
    def __init__(column, name: str = None):
        column.__table: Table = None # noqa
        column.name: str|None = name
        class Descriptor:
            def __init__(descriptor, name):
                descriptor.name = name
            def __set__(descriptor, row, value):
                column.__validate_set([getattr(row, descriptor.name)], [value]) # noqa
                setattr(row, descriptor.name, value)
            def __del__(descriptor, row):
                column.__validate_rem([getattr(row, descriptor.name)]) # noqa
        column.__descriptor = Descriptor(column.name)

    @property
    def table(self):
        return self.__table

    def __validate_add(self, rows: tuple|Column):
        """Validate adding rows to the table."""
        return

    def __validate_rem(self, rows: tuple|Column):
        """Validate removing rows from the table."""
        return

    def __validate_set(self, old: tuple|Column, new: tuple|Column):
        """Validate replacing row data in the table."""
        self.__validate_rem(old)
        self.__validate_add(new)

    def __add(self, rows: tuple|Column):
        """Add rows to the table."""
        return

    def __rem(self, rows: tuple|Column):
        """Remove rows from the table."""
        return

    def __set(self, old: tuple|Column, new: tuple|Column):
        """Replace row data in the table."""
        self.__rem(old)
        self.__add(new)

    def __iter__(self) -> T.Iterator[ElementType]:
        attr = self.name
        return iter(getattr(row, attr) for row in self.__table)

    def __len__(self):
        return len(self.__table)



RowType = T.TypeVar('RowType', bound='Tabular')

class Table(T.Generic[RowType]):
    """Table of rows."""
    __RowSpec: T.Type[RowType] = None
    """Class for rows in the table."""
    __UnvalidatedRowSpec: T.Type[RowType] = None
    """Class for rows in the table without column descriptors for validation"""
    __from_inflexible: Table[RowType]|None = None
    """For flexible tables, backpointer to inflexible version of the table"""
    __id_column: str|None = None
    """Name of the column that is the primary key (str keys) for the table"""
    __sort_column: str|None = None
    """Name of the column that is the sort key for the table"""

    def __init__(self, *datas, **columns):
        self._rows_ = []
        self._meta_ = TableMeta(self)
        self._columns_: dict[str, Column] = {}

    def __iter__(self) -> T.Iterator[RowType]:
        return iter(self._rows_)

    def __len__(self) -> int:
        return len(self._rows_)

    def __call__(self):
        return self._meta_

    def __pos__(self):
        """Copy the table."""
        return ...

    def __invert__(self) -> Table[RowType]:
        """Mark the table as flexible."""
        inverted = self[...]
        inverted.__flexible = True
        inverted.__inflexible = self
        return inverted

    def __enter__(self):
        """Return a version of the table where column invariants are unenforced until exit"""
        return self.__invert__()

    def __exit__(self, exc_type, exc_value, traceback):
        """Validate columns"""
        table = self.__inflexible
        columns = {c: None for n, c in table.__dict__.items() if isinstance(c, Column)}
        for column in reversed(columns):
            column = copy.copy(column)
            column.__table = None
            column.__validate_add(table._rows_)

    def __iadd__(self, other) -> T.Self:
        """Add one or more rows to the table."""
        columns = {c: None for n, c in self.__dict__.items() if isinstance(c, Column)}
        if isinstance(other, Tabular):
            for column in reversed(columns):
                column.__validate_add((getattr(other, column.name),))
            for column in reversed(columns):
                column.__add((getattr(other, column.name),))
            other.__tables__ = wr.WeakSet((self, *other.__tables__))
            self._rows_.append(other)
        elif isinstance(other, dict):
            other_lens = set(len(x) for x in other.values() if isinstance(x, list))
            assert len(other_lens) == 1, \
                "All columns must have the same length and at least one must be non-broadcast"
            other_len, = other_lens
            other = {n: v if isinstance(v, list) else [v] * other_len for n, v in other.items()}
            names, other_columns = list(other.keys()), list(other.values())
            other_data = zip(*other_columns)
            other_rows = [self.__UnvalidatedRowSpec(**dict(zip(names, row))) for row in other_data]
            for column in reversed(columns):
                column.__validate_add([getattr(x, column.name) for x in other_rows])
            for column in reversed(columns):
                column.__add([getattr(x, column.name) for x in other_rows])
            for row in other_rows:
                row.__class__ = self.__RowSpec
                row.__tables__ = wr.WeakSet((self, *row.__tables__))
            self._rows_.extend(other_rows)
        if isinstance(other, list):
            if not other:
                return self
            first = other[0]
            if isinstance(first, Tabular):
                for column in reversed(columns):
                    column.__validate_add([getattr(x, column.name) for x in other])
                for column in reversed(columns):
                    column.__add([getattr(x, column.name) for x in other])
                for row in other:
                    row.__tables__ = wr.WeakSet((self, *row.__tables__))
                self._rows_.extend(other)
            elif isinstance(first, (list, tuple)):
                other_rows = [self.__UnvalidatedRowSpec(*row) for row in other]
                for column in reversed(columns):
                    column.__validate_add([getattr(x, column.name) for x in other_rows])
                for column in reversed(columns):
                    column.__add([getattr(x, column.name) for x in other_rows])
                for row in other_rows:
                    row.__class__ = self.__RowSpec
                    row.__tables__ = wr.WeakSet((self, *row.__tables__))
                self._rows_.extend(other_rows)
            elif isinstance(first, dict):
                other_rows = [self.__UnvalidatedRowSpec(**row) for row in other]
                for column in reversed(columns):
                    column.__validate_add([getattr(x, column.name) for x in other_rows])
                for column in reversed(columns):
                    column.__add([getattr(x, column.name) for x in other_rows])
                for row in other_rows:
                    row.__class__ = self.__RowSpec
                    row.__tables__ = wr.WeakSet((self, *row.__tables__))
                self._rows_.extend(other_rows)
            else:
                raise TypeError(f"Row wise concat does not support {type(other)} of {type(first)}")
        elif isinstance(other, Table):
            for column in reversed(columns):
                column.__validate_add(getattr(other, column.name))
            for column in reversed(columns):
                column.__add(getattr(other, column.name))
            for row in other._rows_:
                row.__tables__ = wr.WeakSet((self, *row.__tables__))
            self._rows_.extend(other._rows_)
        else:
            raise TypeError(f"Row wise concat does not support {type(other)}")
        return self

    def __isub__(self, other) -> T.Self:
        """Add one or more columns to the table."""
        columns = {n: c for n, c in self.__dict__.items() if isinstance(c, Column)}
        if isinstance(other, dict):
            for name, column in list(other.items()):
                assert name not in columns, f"Column {name} already exists in the table"
                if isinstance(column, list):
                    assert len(column) == len(self._rows_), \
                        f"Column {name} must be an iterable of length {len(self._rows_)}"
                else:
                    other[name] = [column] * len(self._rows_)
            for name, column in other.items():
                new_column = Column(name)
                self.__dict__[name] = new_column
                new_column.__table = self
            ...
        elif isinstance(other, Table):
            assert len(other._rows_) == len(self._rows_), \
                "Table must have the same number of rows as the table it is being added to"
            for name, column in other.__dict__.items():
                assert name not in columns, f"Column {name} already exists in the table"
                new_column = Column(name)
                self.__dict__[name] = new_column
                new_column.__table = self
            ...
        elif isinstance(other, Column):
            assert len(other) == len(self._rows_)
            ...
        elif isinstance(other, list):  # anonymous column, auto-name
            assert len(other) == len(self._rows_)
            ...
        else:  # broadcast value to anonymous column
            ...
        return self


    def __getitem__(self, selection) -> Table[RowType] | RowType:
        """Return a view of the table or row"""
        if isinstance(selection, int):
            ...
        elif isinstance(selection, slice):
            ...
        elif isinstance(selection, (Column, ellipsis)):
            view = Table[RowType]()
            self_vars = self.__dict__
            if selection is ...:
                view.__dict__.update(self_vars)
            else:
                view.__dict__.update({
                    var: val for var, val in self_vars.items() if not isinstance(val, Column)})
                view.__dict__[selection.name] = self_vars[selection.name]
            return view
        elif isinstance(selection, (tuple, list)):
            if not selection:
                ...
            else:
                first = selection[0]
                if isinstance(first, int):
                    ...
                elif isinstance(first, slice):
                    ...
                elif isinstance(first, (Column, ellipsis)):
                    column_names = dict.fromkeys([col.name for col in selection if col is not ...])
                    if len(column_names) < len(selection): # if ... in selection
                        all_column_names = {}
                        for column in selection:
                            if column is ...:
                                column_names.update(
                                    c.name for c in self._meta_ if c.name not in column_names)
                            else:
                                all_column_names[column.name] = None
                        column_names = all_column_names
                    view = Table[RowType]()
                    self_vars = self.__dict__
                    view.__dict__.update({
                        var: val for var, val in self_vars.items() if not isinstance(val, Column)})
                    view.__dict__.update({name: self_vars[name] for name in column_names})
                    return view
                else:
                    ...
        elif isinstance(selection, set):
            ...
        else:
            ...
        return ...

    def __setitem__(self, key, value):
        """Switch in new table rows, mutate column-wise, or mutate cell-wise."""
        ...

    def __delitem__(self, key):
        """Remove rows, columns, or data from the table."""
        ...

    def __delattr__(self, item):
        """Remove columns from the table."""
        ...


MetaRowType = T.TypeVar('MetaRowType')
GroupKeyType = T.TypeVar('GroupKeyType')

class TableMeta(T.Generic[MetaRowType]):
    def __init__(self, table: Table[MetaRowType]):
        self.table: Table[MetaRowType] = table

    def columns(self) -> T.Dict[str, Column]:
        return dict(self.table._columns_)

    def __iter__(self) -> T.Iterator[Column]:
        return iter(self.table._columns_.values())

    def __getitem__(self, item: str):
        return self.table._columns_[item]

    def group(self,
        key:T.Iterable[GroupKeyType]|T.Callable[[RowType], GroupKeyType]
    ) -> dict[GroupKeyType, Table[MetaRowType]]:
        """Group rows by some key and return a dict of the groups."""
        return ...


TabularType = T.TypeVar('TabularType', bound='Tabular')

class Tabular:
    """Row type. Inherit from this to create a Table/Row format."""
    __tables__: set[Table] = frozenset()

    @classmethod
    def s(
        cls: T.Type[TabularType],
        *datas: TabularType,
        **columns
    ) -> Table[TabularType]|TabularType:
        table = Table[cls](*datas, **columns)
        table.__RowSpec = cls
        table.__UnvalidatedRowSpec = cls.__unvalidated
        return table

    def __getattr__(self, item):
        setattr(type(self), item, None)
        return None


def tabular_fields(cls) -> dict[str, T.Type]:
    fields = {}
    for field in dc.fields(cls):
        for first_union_type in T.get_args(field.type):
            if Column in getattr(first_union_type, '__mro__', ()):
                fields[field.name] = first_union_type
            break
    return fields

def tabular_spec(cls) -> dict[str, T.Any]:
    fields = {}
    for field in dc.fields(cls):
        for first_union_type in T.get_args(field.type):
            if Column in getattr(first_union_type, '__mro__', ()):
                spec = cls.__dict__[field.name]
                if isinstance(spec, Column):
                    fields[field.name] = spec.__class__
                elif isinstance(spec, type) and issubclass(spec, Column):
                    fields[field.name] = spec
            break
    return fields


TabularDataClassType = T.TypeVar('TabularDataClassType', bound=Tabular)

#@T.dataclass_transform()
def tabular(cls: type[TabularDataClassType]) -> type[TabularDataClassType]:
    cls = dataclass(cls)
    class validated_cls(cls): pass
    fields = tabular_fields(validated_cls)
    class_vars = vars(validated_cls)
    for name, column_type in fields.items():
        descriptor = cls.__descriptor
        if descriptor is not None:
            class_vars[name] = descriptor(name)
    validated_cls.__unvalidated = cls
    return validated_cls


ColElementType = T.TypeVar('ColElementType')
Col = T.Union[Column[ColElementType], ColElementType, None]


if __name__ == '__main__':
    Col()
