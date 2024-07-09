
from __future__ import annotations
import typing as T


''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')
ColumnTableRowType = T.TypeVar('ColumnTableRowType')
OtherColumnTableType = T.TypeVar('OtherColumnTableType')
OtherColumnTableRowType = T.TypeVar('OtherColumnTableRowType')

class Column(T.Generic[ColumnCellType, ColumnTableType]):
    def __init__(self, name=None, tab:ColumnTableType=None):
        self.__table__: ColumnTableType = tab
        self.__attrs__ = ColumnAttrs(self)
        self.__name__ = name

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        ...

    def __sub__(
        self: Column[ColumnCellType, ColumnTableType],
        other: Column[T.Any, OtherColumnTableType]
    ) -> ColumnTableType | OtherColumnTableType:
        ...

    def __call__(self):
        return self


ColumnAttrsType = T.TypeVar('ColumnAttrsType', bound=Column)

class ColumnAttrs(T.Generic[ColumnAttrsType]):
    def __init__(self, col: ColumnAttrsType):
        self.col: ColumnAttrsType = col

    @property
    def table(self):
        return self.col.__table__


''' ============================== Table ============================== '''

TableRowType = T.TypeVar('TableRowType')

class Table:
    def __init__(self, *rows: T.Iterable[T.Self], cols=None, file=None):
        self.__attrs__ = TableAttrs[T.Self](self, cols)
        self.__rows__: list[T.Self] = ...

    def __call__(self):
        return self.__attrs__

    def __iter__(self) -> T.Iterator[T.Self]:
        ...

    def __getitem__(self, item) -> T.Self:
        """Select"""
        return self


TableAttrsType  = T.TypeVar('TableAttrsType')

class TableAttrs(T.Generic[TableAttrsType]):
    def __init__(self, tab: TableAttrsType, cols=None):
        self.tab: TableAttrsType = tab
        self.cols: dict[str, Column[T.Any, TableAttrsType]] = dict(cols)

    def __iter__(self) -> T.Iterator[Column[T.Any, TableAttrsType]]:
        ...

    def __getitem__(self, item) -> Column[T.Any, TableAttrsType]:
        ...

    def save(self):
        ...


''' ============================== Row ============================== '''

def inspect_row_layout(cls) -> dict[str, T.Type]:
    fields = {}
    for field_name, field_type in getattr(cls, '__annotations__', {}).items():
        for first_union_type in T.get_args(field_type):
            if Column in getattr(first_union_type, '__mro__', ()):
                element_types = T.get_args(first_union_type)
                element_type = element_types[0] if element_types else None
                fields[field_name] = element_type
            break
    return fields

def search_type_annotation(annotation):
    yield ...


CellType = T.TypeVar('CellType')
RowType = T.TypeVar('RowType')
Col = T.Union[Column[CellType, RowType], CellType, None]

class RowMeta(type):
    def __new__(mcs, name, bases, attrs):
        bases = tuple(base for base in bases if base is not Table)
        cls = super().__new__(mcs, name, bases, attrs)
        for field, element_type in inspect_row_layout(cls):
            ...
        return cls

class Row(Table, metaclass=RowMeta):
    @classmethod
    def s(cls) -> T.Self:
        return Table()


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

