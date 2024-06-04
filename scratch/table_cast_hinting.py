
from __future__ import annotations
import typing as T


ColumnCellType = T.TypeVar('ColumnCellType')

class Column(T.Generic[ColumnCellType]):

    def __iter__(self) -> T.Iterator[ColumnCellType]:
        pass


TableRowType = T.TypeVar('TableRowType')

class Table(T.Generic[TableRowType]):

    def __iter__(self) -> T.Iterator[TableRowType]:
        pass


class MetaRow(type):
    def __new__(type, name, bases, ns):
        cls = super().__new__(type, name, bases, ns)
        cls.__cls__ = cls
        return cls

class Row(metaclass=MetaRow):
    def s(self=None) -> Table[T.Self]:
        pass


if __name__ == '__main__':

    import dataclasses as dc


    @dc.dataclass
    class Duck(Row):
        name: str
        age: int

        def quack(self):
            return f'{self.name} quack!'


    def main():
        ducks = Duck.s()
        for duck in ducks:
            ...


    main()



