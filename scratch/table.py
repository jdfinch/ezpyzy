from __future__ import annotations
import dataclasses as dc
import textwrap as tw
import copy as cp
from ezpyzy.digital_iteration import digital_iteration
import typing as T

def errmsg(msg): return tw.dedent(msg).strip()


ColumnElementType = T.TypeVar('ColumnElementType')

class Column(T.Generic[ColumnElementType]):
    descriptor = None  # Descriptor for rows when accessing this col as an attriute

    def __init__(self, elements: T.Iterable[ColumnElementType]=None, name: str = None, table: Table = None):
        if not hasattr(elements, '__len__'):
            elements = list(elements)
        self.name = name
        self.table: Table | None = Table() if table is None else table
        self.table.add_column(self)
        self.on_validate_cat({self: elements})
        self.on_cat({self: elements})


    def __len__(self):
        return len(self.table)

    def __iter__(self):
        return iter((getattr(row, self.name) for row in self.table))

    def __getitem__(self, index):
        return getattr(self.table[index], self.name)

    def __setitem__(self, index, value):
        ...

    def __delitem__(self, key):
        assert list(self.table()) == [self], errmsg(f'''
            Cannot delete column elements if the column is part of a table with multiple columns''')
        del self.table[key]

    def on_validate_cat(self, update: dict[Column, T.Sequence[T.Any]]):
        pass

    def on_validate_del(self, update: dict[Column, list[int]]):
        pass

    def on_validate_set(self, update: dict[Column, tuple[list[int], T.Sequence[T.Any]]]):
        pass

    def on_validate_sel(self, update: dict[Column, list[int]]):
        pass

    def on_validate_tab(self, update: dict[Column, bool]):
        pass

    def on_cat(self, update: dict[Column, T.Sequence[T.Any]]):
        pass

    def on_del(self, update: dict[Column, list[int]]):
        pass

    def on_set(self, update: dict[Column, tuple[list[int], T.Sequence[T.Any]]]):
        pass

    def on_sel(self, update: dict[Column, list[int]]):
        pass

    def on_tab(self):
        ...


def tabular_column_types(cls) -> dict[str, T.Type]:
    fields = {}
    for field in dc.fields(cls):
        for first_union_type in T.get_args(field.type):
            if Column in getattr(first_union_type, '__mro__', ()):
                fields[field.name] = first_union_type
            break
    return fields

def tabular_columns(cls) -> dict[str, Column]:
    fields = {}
    for field in dc.fields(cls):
        for first_union_type in T.get_args(field.type):
            if Column in getattr(first_union_type, '__mro__', ()):
                spec = cls.__dict__[field.name]
                if isinstance(spec, Column):
                    fields[field.name] = spec
            break
    return fields


class MetaTable(type):
    validated = True
    validated_version = None
    unvalidated_version = None
    def __new__(cls, name, bases, attrs):
        cls = super().__new__(cls, name, bases, attrs)
        tcs = tabular_columns(cls)
        tcts = tabular_column_types(cls)
        if cls.validated: # noqa
            cls.validated_version = cls
            cls.column_templates = tcs
            cls.column_types = tcts
            for name, column in tcs.items():
                ... # check for id and sort columns
        else:
            cls.column_templates = {name: Column() for name in tcs}
            cls.column_types = tcts
            cls.unvalidated_version = cls
        return cls


class Table(metaclass=MetaTable):
    column_templates = {}  # Column objects
    column_types = {}
    id_column = None
    sort_column = None
    row_type: type = None

    def __init__(self):
        self.rows = []
        self.meta = TableMetadata(self)
        for name, template in self.column_templates.items():
            column = cp.deepcopy(template)
            column.table = self
            setattr(self, name, column)

    def __call__(self):
        return self.meta

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def add_column(self, column: Column):
        columns = self().columns()
        if column.name is None:
            for generic_name in digital_iteration():
                if generic_name not in columns:
                    column.name = generic_name
                    break
        assert column.name not in columns, errmsg(f'''
            Column with name {column.name} already exists in table {self}''')
        setattr(self, column.name, column)

    def __isub__(self, other):
        """Add columns to the table"""
        ...




class TableMetadata:

    def __init__(self, table):
        self.table = table

    def columns(self):
        return {name: column for name, column in self.table.__dict__.items() if isinstance(column, Column)}

    def __len__(self):
        return len(self.columns())

    def __iter__(self):
        return iter(self.columns().values())




class Tabular:
    table_type = Table

    @classmethod
    def s(cls):
        ...

class Row(Tabular):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

Table.row_type = Row



def tabular(cls):
    """Decorator that creates a table spec and returns a tabular row class with that spec"""
    cls = dc.dataclass(cls)
    class ValidatedTable(Table):
        row_type = cls
    class UnvalidatedTable(Table):
        validated = False
        row_type = cls
    ValidatedTable.unvalidated_version = UnvalidatedTable
    UnvalidatedTable.validated_version = ValidatedTable
    cls.table_type = ValidatedTable
    return cls

