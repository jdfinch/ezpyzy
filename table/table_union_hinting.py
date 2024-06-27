
from __future__ import annotations
import typing as T


''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')

class Column(T.Generic[ColumnCellType, ColumnTableType]):
    def __init__(self, name=None, tab:ColumnTableType=None):
        self.__table__: ColumnTableType = tab
        self.__attrs__ = ColumnAttrs(self)
        self.__name__ = name
        self.__serial__ = ...  # (encoder, decoder)

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        ...

    def __call__(self):
        return self


ColumnAttrsType = T.TypeVar('ColumnAttrsType', bound=Column)

class ColumnAttrs(T.Generic[ColumnAttrsType]):
    def __init__(self, col: ColumnAttrsType):
        self.col: ColumnAttrsType = col

    @property
    def table(self):
        return self.col


''' ============================== Table ============================== '''

TableRowType = T.TypeVar('TableRowType')

class Table(T.Generic[TableRowType]):
    def __init__(self):
        self.__attrs__ = TableAttrs(self)

    def __iter__(self) -> T.Iterator[TableRowType]:
        ...

    def __getattr__(self, column) -> Column[T.Self]:
        return ...

    def __call__(self):
        return self.__attrs__


TableAttrsType  = T.TypeVar('TableAttrsType')

class TableAttrs(T.Generic[TableAttrsType]):
    def __init__(self, tab: TableAttrsType):
        self.tab: TableAttrsType = tab

    def save(self):
        ...


''' ============================== Row ============================== '''

CellType = T.TypeVar('CellType')
Col = T.Union[Column[CellType], CellType, None]

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


def inspect_row_layout(cls) -> dict[str, T.Type]:
    fields = {}
    for field_name, field_type in cls.__annotations__.items():
        for first_union_type in T.get_args(field_type):
            if Column in getattr(first_union_type, '__mro__', ()):
                element_types = T.get_args(first_union_type)
                element_type = element_types[0] if element_types else None
                fields[field_name] = element_type
            break
    return fields

def search_type_annotation(annotation):
    yield ...


''' ============================== Usage ============================== '''
if __name__ == '__main__':
    import dataclasses as dc

    @dc.dataclass
    class Duck(Row):
        name: Col[str]
        age: Col[int]
        children: Col[list[str]]

        def quack(self):
            return f'{self.name} quack!'


    def main():
        ducks = Duck.s()
        for duck in ducks:
            duck.quack()
        for children in ducks.children():
            ...

        # ducks().save()
        # duck = ducks[0]
        # table = duck().tab()
        
    main()

