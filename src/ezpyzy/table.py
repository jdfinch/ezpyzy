import typing


T = typing.TypeVar('T')
U = typing.TypeVar('U')
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
        if by is None:
            filtered = list(self.rows)
        elif callable(by):
            filtered = [item for item in self if by(item)]
        elif isinstance(by, (dict, set)):
            if self._id_function is None:
                filtered = [item for item in self if item in by]
            else:
                filtered = [item for item in self if self._id_function(item) in by]
        else:
            items_and_matches = [(item, match) for item, match in zip(self, by)]
            assert len(items_and_matches) == len(self), (
                f"Filter by sequence must be the same length as the Table"
            )
            filtered = [item for item, match in items_and_matches if match]
        self.rows[:] = filtered
        if self._id_function is not None:
            self.ids.clear()
            self.ids.update((self._id_function(item), item) for item in self.rows)
        return self
    
    def select(self, ids: typing.Collection) -> 'Table[T]':
        """Produce a new Table from this Table's rows by ids"""
        assert self._id_function is not None, f"Cannot select by id from a Table with no id_function"
        selected = self.__class__(key=self._id_function)
        for key in ids:
            selected.append(self.ids[key])
        return selected
    
    def __getitem__(self, indices: int|slice|typing.Sequence[int]) -> 'Table[T]':
        sliced = self.__class__(key=self._id_function)
        if isinstance(indices, slice):
            sliced.extend(self.rows[indices])
        elif isinstance(indices, int):
            sliced.append(self.rows[indices])
        else:
            for index in indices:
                sliced.append(self.rows[index])
        return sliced
    
    def slice(self, indices: int|slice|typing.Sequence[int]) -> 'Table[T]':
        sliced = self[indices]
        self.rows[:] = sliced.rows
        if self._id_function is not None:
            self.ids.clear()
            self.ids.update(sliced.ids)
        return self

    def group(self, by: typing.Callable[[T], G]) -> dict[G, 'Table[T]']:
        groups = {}
        for item in self:
            key = by(item)
            if key not in groups:
                groups[key] = self.__class__(key=self._id_function)
            groups[key].append(item)
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
    
    def discard(self, ids: typing.Iterable[typing.Hashable]) -> 'Table[T]':
        assert self._id_function is not None, f"Cannot discard by id from a Table with no id_function"
        discarded = set(ids)
        self.rows[:] = [item for item in self.rows if self._id_function(item) not in discarded]
        self.ids.clear()
        self.ids.update((self._id_function(item), item) for item in self.rows)
        return self

    def remove(self, ids: typing.Iterable[typing.Hashable]) -> 'Table[T]':
        assert self._id_function is not None, f"Cannot remove by id from a Table with no id_function"
        removed = set(ids)
        missing = removed.difference(self.ids)
        assert not missing, f"Items with IDs {missing} do not exist."
        self.rows[:] = [item for item in self.rows if self._id_function(item) not in removed]
        self.ids.clear()
        self.ids.update((self._id_function(item), item) for item in self.rows)
        return self

    def delete(self, indices: typing.Union[int, 'slice', typing.Sequence[int]]) -> 'Table[T]':
        if isinstance(indices, int):
            del self.rows[indices]
        elif isinstance(indices, slice):
            del self.rows[indices]
        else:
            normalized = []
            for index in indices:
                normalized.append(index if index >= 0 else len(self.rows) + index)
            missing = [index for index in normalized if index < 0 or index >= len(self.rows)]
            if missing:
                raise IndexError(f"Table deletion index out of range: {missing[0]}")
            for index in sorted(set(normalized), reverse=True):
                del self.rows[index]
        if self._id_function is not None:
            self.ids.clear()
            self.ids.update((self._id_function(item), item) for item in self.rows)
        return self

    def __delitem__(self, indices: typing.Union[int, 'slice', typing.Sequence[int]]):
        self.delete(indices)

    def _join_index(
        self,
        other: 'Table[U]',
        against: typing.Callable[[U], typing.Hashable]|None,
    ) -> dict[typing.Hashable, list[tuple[int, U]]]:
        if against is None:
            assert other.id_function is not None, (
                f"Cannot join against a Table with no id_function without an against selector"
            )
            against = other.id_function
        index = {}
        for i, item in enumerate(other):
            key = against(item)
            index.setdefault(key, []).append((i, item))
        return index

    def join(
        self,
        other: 'Table[U]',
        on: typing.Callable[[T], typing.Hashable],
        against: typing.Callable[[U], typing.Hashable]|None = None,
    ) -> 'Table[tuple[T, U|None]]':
        return self.join_left(other, on, against)

    def join_inner(
        self,
        other: 'Table[U]',
        on: typing.Callable[[T], typing.Hashable],
        against: typing.Callable[[U], typing.Hashable]|None = None,
    ) -> 'Table[tuple[T, U]]':
        right_index = self._join_index(other, against)
        joined = Table()
        for left in self:
            key = on(left)
            for _, right in right_index.get(key, ()):
                joined.append((left, right))
        return joined

    def join_left(
        self,
        other: 'Table[U]',
        on: typing.Callable[[T], typing.Hashable],
        against: typing.Callable[[U], typing.Hashable]|None = None,
    ) -> 'Table[tuple[T, U|None]]':
        right_index = self._join_index(other, against)
        joined = Table()
        for left in self:
            key = on(left)
            matches = right_index.get(key)
            if matches:
                for _, right in matches:
                    joined.append((left, right))
            else:
                joined.append((left, None))
        return joined

    def join_right(
        self,
        other: 'Table[U]',
        on: typing.Callable[[T], typing.Hashable],
        against: typing.Callable[[U], typing.Hashable]|None = None,
    ) -> 'Table[tuple[T|None, U]]':
        if against is None:
            assert other.id_function is not None, (
                f"Cannot join against a Table with no id_function without an against selector"
            )
            against = other.id_function
        left_index = {}
        for left in self:
            key = on(left)
            left_index.setdefault(key, []).append(left)
        joined = Table()
        for right in other:
            key = against(right)
            matches = left_index.get(key)
            if matches:
                for left in matches:
                    joined.append((left, right))
            else:
                joined.append((None, right))
        return joined

    def join_outer(
        self,
        other: 'Table[U]',
        on: typing.Callable[[T], typing.Hashable],
        against: typing.Callable[[U], typing.Hashable]|None = None,
    ) -> 'Table[tuple[T|None, U|None]]':
        right_index = self._join_index(other, against)
        joined = Table()
        matched_right_indices = set()
        for left in self:
            key = on(left)
            matches = right_index.get(key)
            if matches:
                for i, right in matches:
                    matched_right_indices.add(i)
                    joined.append((left, right))
            else:
                joined.append((left, None))
        for i, right in enumerate(other):
            if i not in matched_right_indices:
                joined.append((None, right))
        return joined

    def join_cartesian(self, other: 'Table[U]') -> 'Table[tuple[T, U]]':
        joined = Table()
        for left in self:
            for right in other:
                joined.append((left, right))
        return joined

    def _row_attributes(self, row) -> list[str]:
        if isinstance(row, dict):
            return list(row)
        if isinstance(row, (tuple, list)):
            return []
        if hasattr(row, '__dict__'):
            return list(vars(row))
        if hasattr(type(row), '__annotations__'):
            return list(type(row).__annotations__)
        if hasattr(type(row), '__slots__'):
            slots = type(row).__slots__
            if isinstance(slots, str):
                return [slots]
            return list(slots)
        return []

    def _row_value(self, row, attribute: str):
        if isinstance(row, dict):
            return row[attribute]
        return getattr(row, attribute)

    def render(
        self,
        rows: int|None = None,
        width=100,
        cols: dict[str, str|bool|typing.Callable[[T], typing.Any]]|None = None,
        cell_width: int = 10,
    ) -> str:
        rows_ = list(self.rows)
        if not rows_:
            return ''
        displayed_rows = rows_ if rows is None else rows_[:rows]

        tuple_rows = all(isinstance(row, (tuple, list)) for row in displayed_rows)
        if tuple_rows:
            max_length = max(len(row) for row in displayed_rows)
            inferred = {str(i): (lambda row, i=i: row[i] if i < len(row) else None) for i in range(max_length)}
        else:
            inferred = {}
            for row in displayed_rows:
                for attribute in self._row_attributes(row):
                    if attribute not in inferred:
                        inferred[attribute] = (
                            lambda row, attribute=attribute: self._row_value(row, attribute)
                        )

        if cols:
            columns = dict(inferred)
            for column, spec in cols.items():
                if spec is False:
                    columns.pop(column, None)
                elif spec is True:
                    columns[column] = lambda row, column=column: self._row_value(row, column)
                elif isinstance(spec, str):
                    columns.pop(spec, None)
                    columns[column] = lambda row, spec=spec: self._row_value(row, spec)
                else:
                    columns[column] = spec
        else:
            columns = inferred

        headers = list(columns)
        rendered_rows = []
        for row in displayed_rows:
            rendered_row = []
            for getter in columns.values():
                try:
                    value = getter(row)
                except (AttributeError, KeyError, IndexError, TypeError):
                    value = None
                rendered_row.append(str(value))
            rendered_rows.append(rendered_row)

        widths = [len(header) for header in headers]
        for rendered_row in rendered_rows:
            for i, cell in enumerate(rendered_row):
                widths[i] = max(widths[i], len(cell))

        separator_width = 3 * max(len(headers) - 1, 0)
        if sum(widths) + separator_width > width:
            widths = [max(len(header), min(cell_width, column_width)) for header, column_width in zip(headers, widths)]

        visible_headers = []
        visible_widths = []
        visible_rows = [[] for _ in rendered_rows]
        omitted_columns = False
        for i, (header, column_width) in enumerate(zip(headers, widths)):
            if visible_headers:
                next_width = sum(visible_widths) + 3 * len(visible_headers) + column_width
            else:
                next_width = column_width
            if next_width <= width:
                visible_headers.append(header)
                visible_widths.append(column_width)
                for rendered_row, visible_row in zip(rendered_rows, visible_rows):
                    visible_row.append(rendered_row[i])
            else:
                omitted_columns = True
                break

        if not visible_headers and headers:
            visible_headers = [headers[0]]
            visible_widths = [min(max(len(headers[0]), 2), width)]
            visible_rows = [[rendered_row[0]] for rendered_row in rendered_rows]
            omitted_columns = len(headers) > 1

        if omitted_columns and visible_headers:
            ellipsis_width = 2
            while visible_headers and sum(visible_widths) + 3 * len(visible_headers) + ellipsis_width > width:
                visible_headers.pop()
                visible_widths.pop()
                for visible_row in visible_rows:
                    if visible_row:
                        visible_row.pop()
            if visible_headers and sum(visible_widths) + 3 * len(visible_headers) + ellipsis_width <= width:
                visible_headers.append('..')
                visible_widths.append(ellipsis_width)
                for visible_row in visible_rows:
                    visible_row.append('..')
            else:
                visible_headers = ['..']
                visible_widths = [min(2, width)]
                visible_rows = [['..'] for _ in rendered_rows]

        def fit(cell: str, width_for_cell: int) -> str:
            if len(cell) <= width_for_cell:
                return cell.ljust(width_for_cell)
            if width_for_cell <= 2:
                return '.' * width_for_cell
            return f"{cell[:width_for_cell - 2]}..".ljust(width_for_cell)

        type_names = []
        for row in rows_:
            name = type(row).__name__
            if name not in type_names:
                type_names.append(name)
        title = f"Table of {', '.join(type_names)} with {len(rows_)} rows"
        if len(title) > width:
            title = fit(title, width)

        header = ' | '.join(fit(cell, column_width) for cell, column_width in zip(visible_headers, visible_widths))
        divider = '-+-'.join('-' * column_width for column_width in visible_widths)
        body = [
            ' | '.join(fit(cell, column_width) for cell, column_width in zip(rendered_row, visible_widths))
            for rendered_row in visible_rows
        ]
        return '\n'.join([title, header, divider, *body])

    def display(
        self,
        rows: int|None = None,
        width=100,
        cols: dict[str, str|bool|typing.Callable[[T], typing.Any]]|None = None,
        cell_width: int = 10,
    ) -> str:
        rendered = self.render(rows=rows, width=width, cols=cols, cell_width=cell_width)
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

    table.display(width=30)
