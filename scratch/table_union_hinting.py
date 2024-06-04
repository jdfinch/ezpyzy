
from __future__ import annotations
import typing as T


''' ============================== Column ============================== '''

ColumnCellType = T.TypeVar('ColumnCellType')
ColumnTableType = T.TypeVar('ColumnTableType')

class Column(T.Generic[ColumnCellType]):
    def __init__(self, name=None, tab:ColumnTableType=None):
        self.__tab__ = tab
        self.__meta__ = ColumnMeta(self)

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        ...

    def __call__(self):
        return self.__meta__


ColumnMetaColumnType = T.TypeVar('ColumnMetaColumnType', bound=Column)

class ColumnMeta(T.Generic[ColumnMetaColumnType]):
    def __init__(self, col: ColumnMetaColumnType):
        self.col: ColumnMetaColumnType = col

    @property
    def tab(self):
        return self.col



''' ============================== Table ============================== '''

CellType = T.TypeVar('CellType')
Col = T.Union[Column[CellType], CellType, None]

TableRowType = T.TypeVar('TableRowType')

class Table(T.Generic[TableRowType]):
    def __init__(self):
        self.__meta__ = TableMeta(self)

    def __iter__(self) -> T.Iterator[TableRowType]:
        ...

    def __call__(self):
        return self.__meta__


TableMetaTableType  = T.TypeVar('TableMetaTableType')

class TableMeta(T.Generic[TableMetaTableType]):
    def __init__(self, tab: TableMetaTableType):
        self.tab: TableMetaTableType = tab

    def save(self):
        ...


class Row:
    @classmethod
    def s(cls) -> Table[T.Self] | T.Self:
        pass



''' ============================== Usage ============================== '''
if __name__ == '__main__':
    import dataclasses as dc

    @dc.dataclass
    class Duck(Row):
        name: Col[str]
        age: Col[int]

        def quack(self):
            return f'{self.name} quack!'


    def main():
        ducks = Duck.s()
        for duck in ducks:
            duck.quack()
        for age in ducks.age:
            age.real

        # ducks().save()
        # duck = ducks[0]
        # table = duck().tab()
        
    main()

