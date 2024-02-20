from __future__ import annotations
import dataclasses as dc
from dataclasses import dataclass
import copy
import typing as T


def column_get(name):
    name = '__'+name
    def get(self: Tabular):
        return getattr(self, name)
    return get

def column_set(name):
    name = '__'+name
    def set(self: Tabular, value):
        setattr(self, name, value)
    return set

def column_del(name):
    name = '__'+name
    def delete(self: Tabular):
        delattr(self, name)
    return delete



ElementType = T.TypeVar('ElementType')

class Column(T.Generic[ElementType]):
    __get = None
    __set = None
    __del = None

    def __init__(self):
        self.table: Table = None # noqa
        self.name: str = None # noqa

    def __iter__(self) -> T.Iterator[ElementType]:
        attr = self.name
        return iter(getattr(row, attr) for row in self.table)


RowType = T.TypeVar('RowType', bound='Tabular')

class Table(T.Generic[RowType]):
    """Table of rows."""
    __RowSpec: T.Type[RowType] = None
    __flexible: bool = False

    def __init__(self, *datas, **columns):
        self.__rows = []
        self.__meta = TableMeta(self)

    def __iter__(self) -> T.Iterator[RowType]:
        return iter(self.__rows)

    def __len__(self) -> int:
        return len(self.__rows)

    def __call__(self):
        return self.__meta

    def __pos__(self):
        """Copy the table."""
        return ...

    def __invert__(self) -> Table[RowType]:
        """Mark the table as concatenate-flexible."""
        inverted = self[...]
        inverted.__flexible = True
        return inverted

    def __iadd__(self, other) -> T.Self:
        """Add one or more rows to the table."""
        if isinstance(other, (list, tuple)):
            if not other:
                return self
            first = other[0]
            if isinstance(first, (list, tuple)):
                self.__rows.extend([self.__RowSpec(*row) for row in other])
            elif isinstance(first, Tabular):
                self.__rows.extend(other)
            elif isinstance(first, dict):
                self.__rows.extend([self.__RowSpec(**row) for row in other])
            else:
                raise TypeError(f"Row wise concat does not support {type(other)} of {type(first)}")
        elif isinstance(other, Table):
            ...
        elif isinstance(other, dict):
            ...
        else:
            raise TypeError(f"Row wise concat does not support {type(other)}")
        return self

    def __isub__(self, other) -> T.Self:
        """Add one or more columns to the table."""
        if isinstance(other, dict):
            for name, column in other.items():
                if column is None: # fill with None
                    ...
                else:
                    ...
        elif isinstance(other, Table):
            assert len(other.__rows) == len(self.__rows)
            ...
        elif isinstance(other, Column):
            ...
        elif isinstance(other, (list, tuple)):  # anonymous column, auto-name
            assert len(other) == len(self.__rows)
            ...
        else:                                   # anonymous column with broadcasted value
            ...
        return ...


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
                                    c.name for c in self.__meta if c.name not in column_names)
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

empty_table = Table()


MetaRowType = T.TypeVar('MetaRowType')
GroupKeyType = T.TypeVar('GroupKeyType')

class TableMeta(T.Generic[MetaRowType]):
    def __init__(self, table: Table[MetaRowType]):
        self.table: Table[MetaRowType] = table

    def columns(self) -> T.List[Column]:
        non_column_attrs = vars(empty_table)
        return [
            col for attr, col in vars(self.table).items()
            if attr not in non_column_attrs]

    def __iter__(self) -> T.Iterator[Column]:
        return iter(self.columns())

    def group(self,
        key:T.Iterable[GroupKeyType]|T.Callable[[RowType], GroupKeyType]
    ) -> dict[GroupKeyType, Table[MetaRowType]]:
        """Group rows by some key and return a dict of the groups."""
        return ...


TabularType = T.TypeVar('TabularType')

class Tabular:
    """Row type. Inherit from this to create a Table/Row format."""
    __table__:Table|None = None

    @classmethod
    def s(cls: T.Type[TabularType], *datas, **columns) -> Table[TabularType]|TabularType:
        table = Table[cls](*datas, **columns)
        table.__RowSpec = cls
        return table

    def __getattr__(self, item):
        setattr(type(self), item, None)
        return None


def tabular_fields(cls):
    fields = {}
    for field in dc.fields(cls):
        for first_union_type in T.get_args(field.type):
            if Column in getattr(first_union_type, '__mro__', ()):
                fields[field.name] = first_union_type
            break
    return fields


TabularDataClassType = T.TypeVar('TabularDataClassType')

@T.dataclass_transform()
def tabular(cls: type[TabularDataClassType]) -> type[TabularDataClassType]:
    cls = dataclass(cls)
    class_vars = vars(cls)
    fields = tabular_fields(cls)
    for name, column_type in fields.items():
        if any(x is not None for x in (column_type.__get, column_type.__set, column_type.__del)):
            class_vars[name] = property(
                column_type.__get(name),
                column_type.__set(name),
                column_type.__del(name)
            )
    return cls


ColElementType = T.TypeVar('ColElementType')
Col = T.Union[Column[ColElementType], ColElementType, None]