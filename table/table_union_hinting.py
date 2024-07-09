
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
        self.__table__: ColumnTableType[ColumnTableRowType] = tab
        self.__attrs__ = ColumnAttrs(self)
        self.__name__ = name

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        ...

    def __sub__(self, other: Column[T.Any, OtherColumnTableType[OtherColumnTableRowType]]
    ) -> ColumnTableType | ColumnTableRowType | OtherColumnTableType | OtherColumnTableRowType:
        return ...

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

class Table(T.Generic[TableRowType]):
    def __init__(self, *rows: T.Iterable[TableRowType], cols=None, file=None):
        self.__attrs__ = TableAttrs[T.Self](self, cols)
        self.__rows__: list[TableRowType] = ...
        self._: Table[TableRowType] | TableRowType = self

    def __call__(self):
        return self.__attrs__

    def __iter__(self) -> T.Iterator[TableRowType]:
        ...

    def __getitem__(self, item) -> Table[TableRowType] | TableRowType:
        """Select"""
        if isinstance(item, (int, slice)):
            return Table(self.__rows__[item], cols=self.__attrs__.cols)


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
Col = T.Union[Column[CellType, Table[RowType]], CellType, None]
ColCellType = T.TypeVar('ColCellType')
ColType = Col[ColCellType]

class RowMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        for field, element_type in inspect_row_layout(cls):
            ...
        return cls

class Row(metaclass=RowMeta):
    @classmethod
    def s(cls) -> Table[T.Self] | T.Self:
        pass


''' ============================== Usage ============================== '''
if __name__ == '__main__':
    import dataclasses as dc

    CTRT = T.TypeVar('CTRT')
    CTET = T.TypeVar('CTET')

    class ColType(T.Generic[CTRT]):
        def __call__(self, ctet: type[CTET]) -> Column[Table[CTRT], CTET] | CTET | None:
            return None

    C = T.TypeVar('C')

    D: T.TypeAlias = 'Duck'
    @dc.dataclass
    class Duck(Row):
        name: Col[str, D]
        age: Col[int, Duck]
        children: Col[list[str], Duck]

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

        some_ducks = ducks[1:4]._
        duck_attrs = ducks[:,3]
        more_ducks = ducks[:,:]
        duck_column = ducks[ducks.name]

        second_col = ducks()[1:2]

        names = ducks.name
        ages = ducks.age
        names_and_ages = (names-ages)

        
    main()

