
import typing


T = typing.TypeVar('T')
G = typing.TypeVar('G')
A = typing.TypeVar('A')
E = typing.TypeVar('E')
R = typing.TypeVar('R')


class Table(typing.Generic[T]):

    def __init__(self, *items: typing.Iterable[T], key:typing.Callable[[T], typing.Hashable] = None):
        self.rows = []
        if key:
            self.ids = {}
            self._id_function = key
        else:
            self.ids = None
            self._id_function = None
        for items in items:
            self.extend(items)

    @property
    def id_function(self):
        return self._id_function
    
    @id_function.setter
    def id_function(self, id_function: typing.Callable[[T], typing.Hashable]|None):
        if id_function is None:
            self.ids = None
            self._id_function = None
        else:
            ids = {id_function(item): item for item in self}
            assert len(ids) == len(self), f"Hash collision created by new id_function"
            self.ids = ids
            self._id_function = id_function
    
    def add(self, item: T):
        """Add an item to the Table, removing any existing items with its ID, at a given index"""
        if self._id_function:
            key = self._id_function(item)
            if key not in self.ids:
                self.ids[key] = len(self)
                self.rows.append(item)
            else:
                pass
        else:
            self.rows.append(item)

    def insert(self, item: T, index: int):
        """Add an item to the Table, if its ID does not already exist in the table"""
        if self._id_function:
            key = self._id_function(item)
            assert key not in self.ids, f"Item with ID {key} already exists."
            self.ids[key] = index
            for i in range(index, len(self.rows)):
                self.ids[self._id_function(self.rows[i])] += 1
            self.rows.insert(index, item)
        else:
            self.rows.insert(item, index)    

    def append(self, item: T):
        """Add an item to the Table, erroring if an item that already has its ID exists."""
        if self._id_function:
            key = self._id_function(item)
            assert key not in self.ids, f"Item with ID {key} already exists."
            self.ids[key] = item
        self.rows.append(item)
        return self

    def extend(self, items: typing.Iterable[T]):
        """Add items to the Table, erroring if an item that already has one of their IDs exists."""
        if self._id_function:
            keys = [self._id_function(item) for item in items]
            for key in keys:
                assert key not in self.ids, f"Item with ID {key} already exists."
            self.ids.update(zip(keys, items))
        self.rows.extend(items)
        return self

    def update(self, items: typing.Iterable[T]):
        """Add items to the Table, ignoring items whose IDs are already in the Table"""
        if self._id_function:
            keys = (self._id_function(item) for item in items)
            for key, item in zip(keys, items):
                if key not in self.ids:
                    self.ids[key] = len(self.rows)
                    self.rows.append(item)
        else:
            self.rows.extend(items)
        return self

    def __iter__(self):
        return iter(self.rows)
    
    def __len__(self):
        return len(self.rows)

    def try_get(self, getter: typing.Callable[[T], A]) -> 'Table[A]':
        """Produce a new Table by attempting to apply a predicate over each row of this table"""
        result = Table()
        for row in self:
            try:
                attr = getter(row)
                result.append(attr)
            except (KeyError, IndexError) as e:
                result.append(None)
            except AttributeError as e:
                if e.obj is not None:
                    raise
                else:
                    result.append(None)
            except TypeError as e:
                if e.args[0].startswith("'NoneType'"):
                    result.append(None)
                else:
                    raise
        return result
    
    def get(self, getter: typing.Callable[[T], E]) -> 'Table[E]':
        """Produce a new Table by applying a predicate over each row of this table"""
        gotten = self.__class__()
        gotten.extend(getter(item) for item in self)
        return gotten

    def filter(
        self,
        by: typing.Callable[[T], bool]|typing.Sequence[bool]|dict|set = None
    ) -> 'Table[T]':
        """Filter rows to leave only those with a True predicate, or with IDs in the dict/set"""
    
    def select(self, ids: typing.Collection) -> 'Table[T]':
        """Produce a new Table from this Table's rows by ids"""
    
    def group(self, by: typing.Callable[[T], G]) -> dict[G, 'Table[T]']:
        groups = {}
        for item in self:
            key = by(item)
            groups.setdefault(key, self.__class__(key=self._id_function)).append(item)
        return groups

    def sort(self, by: typing.Callable[[T], typing.Any]|typing.Iterable, reverse=False):
        if not callable(by):
            items_and_keys = [(item, key) for item, key in zip(self, by)]
            assert len(items_and_keys) == len(self), f"Sort by sequence must be the same length as the Table"
            items_and_keys.sort(key=lambda x: x[1], reverse=reverse)
            self.rows = [item for item, key in items_and_keys]
        else:
            self.rows.sort(key=by, reverse=reverse)
        return self
    
    def delete(self, keys: typing.Iterable):
        for key in keys:
            ...

    # join_inner

    # join_left

    # join_right

    # join_outer

    # join_cartesian


    def render(self, columns: dict[str, typing.Callable[[T], typing.Any]]) -> str:
        ...

    def display(self, columns: dict[str, typing.Callable[[T], typing.Any]]) -> str:
        rendered = self.render(columns)
        print(rendered)
        return rendered




if __name__ == '__main__':

    from dataclasses import dataclass

    @dataclass
    class Foo:
        bar: list[str]|None = None
        bat: typing.Optional['Foo'] = None

        def __call__(self, *args, **kwds):
            return 5

    a = Foo(['hello', 'world'])
    b = Foo(['world', 'war', 'peace'])
    c = Foo(['h', 'w'], a)

    table = Table((a, b, c)) 
    print(f"{list(table.get(lambda x: x.bar[0])) = }")
    print(f"{list(table.get(lambda x: x.bar[1].capitalize())) = }")
    print(f"{list(table.get(lambda x: x.bat)) = }")




