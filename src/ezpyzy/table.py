"""Lightweight typed tables for row-oriented Python data.

`Table` is a small container around a list of row objects. Rows may be plain
Python objects, dataclasses, dict-like objects, tuples, or lists depending on
the operation being used. A table can optionally be keyed by a key function,
which enables fast id-based lookup, selection, and deletion.

The design is intentionally simple:

- positional operations work on row indices
- id-based operations require `key=`
- mutating methods preserve `rows` and `ids` container identity where practical
- joins return tuple rows rather than synthesizing merged objects
- rendering is intended for readable debugging and console inspection
"""

import typing


T = typing.TypeVar('T')
U = typing.TypeVar('U')
G = typing.TypeVar('G')
A = typing.TypeVar('A')
E = typing.TypeVar('E')
R = typing.TypeVar('R')


class Table(typing.Generic[T]):
    """A row-oriented container with optional id-based indexing.

    Parameters
    ----------
    *items:
        Zero or more iterables of rows to load into the table.
    key:
        Optional callable that maps each row to a unique hashable id. When
        provided, `Table.ids` is maintained as a `{id: index}` mapping.

    Notes
    -----
    `Table.rows` is the underlying row list.
    `Table.ids` is either `None` or a `{id: index}` mapping.

    Most methods are intentionally split into positional and id-based forms:

    - positional: `__getitem__`, `slice`, `delete`
    - id-based: `get`, `try_get`, `select`, `discard`, `remove`
    - projection: `map`, `try_map`
    """

    def __init__(self, *items: typing.Iterable[T], key:typing.Callable[[T], typing.Hashable] = None):
        self.rows = []
        if key:
            self.ids = {}
            self._key = key
        else:
            self.ids = None
            self._key = None
        for items in items:
            self.extend(items)

    @property
    def key(self):
        """Return the key function used by this table, if any."""
        return self._key
    
    @key.setter
    def key(self, key: typing.Callable[[T], typing.Hashable]|None):
        """Set or clear the table's key function.

        Setting a key function rebuilds `ids` from the current rows and requires
        the computed ids to be unique.
        """
        if key is None:
            self.ids = None
            self._key = None
        else:
            ids = {key(item): i for i, item in enumerate(self)}
            assert len(ids) == len(self), f"Hash collision created by new key"
            self.ids = ids
            self._key = key
    
    def add(self, item: T):
        """Append a row unless its id is already present.

        On keyed tables, duplicate ids are ignored.
        On unkeyed tables, this behaves like `list.append`.
        """
        if self._key:
            key = self._key(item)
            if key not in self.ids:
                self.ids[key] = len(self)
                self.rows.append(item)
            else:
                pass
        else:
            self.rows.append(item)

    def insert(self, item: T, index: int):
        """Insert a row at a positional index.

        On keyed tables, the row id must not already exist.
        """
        if self._key:
            key = self._key(item)
            assert key not in self.ids, f"Item with ID {key} already exists."
            self.rows.insert(index, item)
            self.ids.clear()
            self.ids.update((self._key(row), i) for i, row in enumerate(self.rows))
        else:
            self.rows.insert(index, item)

    def append(self, item: T):
        """Append a row and error if its id already exists."""
        if self._key:
            key = self._key(item)
            assert key not in self.ids, f"Item with ID {key} already exists."
            self.ids[key] = len(self)
        self.rows.append(item)
        return self

    def extend(self, items: typing.Iterable[T]):
        """Append multiple rows and error on duplicate ids."""
        items = list(items)
        if self._key:
            keys = [self._key(item) for item in items]
            for key in keys:
                assert key not in self.ids, f"Item with ID {key} already exists."
            self.ids.update((key, i) for i, key in enumerate(keys, start=len(self.rows)))
        self.rows.extend(items)
        return self

    def update(self, items: typing.Iterable[T]):
        """Append multiple rows, ignoring any keyed duplicates already present."""
        items = list(items)
        if self._key:
            for item in items:
                key = self._key(item)
                if key not in self.ids:
                    self.ids[key] = len(self.rows)
                    self.rows.append(item)
        else:
            self.rows.extend(items)
        return self

    def __iter__(self):
        """Iterate over rows in order."""
        return iter(self.rows)
    
    def __len__(self):
        """Return the number of rows."""
        return len(self.rows)

    def copy(self) -> 'Table[T]':
        """Return a shallow copy of the table, preserving the key function."""
        copied = self.__class__(key=self._key)
        copied.extend(self.rows)
        return copied

    def clear(self) -> 'Table[T]':
        """Remove all rows in place while preserving container identity."""
        self.rows.clear()
        if self._key is not None:
            self.ids.clear()
        return self

    def try_map(self, getter: typing.Callable[[T], A]) -> 'Table[A]':
        """Map rows into a new table, returning `None` for common missing-value errors.

        This is useful for attribute and item access chains where intermediate
        values may be missing or `None`.
        """
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
    
    def map(self, getter: typing.Callable[[T], E]) -> 'Table[E]':
        """Map rows into a new table by applying a callable to each row."""
        gotten = self.__class__()
        gotten.extend(getter(item) for item in self)
        return gotten

    def get(self, key: typing.Hashable) -> T:
        """Fetch a single row by id.

        Requires the table to be keyed. Missing ids raise `KeyError`.
        """
        assert self._key is not None, f"Cannot get by id from a Table with no key"
        return self.rows[self.ids[key]]

    def try_get(self, key: typing.Hashable) -> T|None:
        """Fetch a single row by id, returning `None` when the id is absent."""
        assert self._key is not None, f"Cannot get by id from a Table with no key"
        if key not in self.ids:
            return None
        return self.rows[self.ids[key]]

    def keys(self):
        """Return row ids in row order."""
        assert self._key is not None, f"Cannot get keys from a Table with no key"
        return self.ids.keys()

    def items(self):
        """Iterate over `(id, row)` pairs in row order."""
        assert self._key is not None, f"Cannot get items from a Table with no key"
        return zip(self.ids.keys(), self.rows)

    def has(self, key: typing.Hashable) -> bool:
        """Return whether an id exists in the table."""
        assert self._key is not None, f"Cannot check ids on a Table with no key"
        return key in self.ids

    def filter(
        self,
        by: typing.Callable[[T], bool]|typing.Sequence[bool]|dict|set = None
    ) -> 'Table[T]':
        """Filter rows in place.

        Supported inputs:

        - predicate callable: keep rows where the predicate is truthy
        - boolean sequence: keep rows paired with a truthy flag
        - dict or set: on keyed tables, keep rows whose ids are members;
          on unkeyed tables, keep rows that are direct members
        - `None`: keep all rows unchanged
        """
        if by is None:
            filtered = list(self.rows)
        elif callable(by):
            filtered = [item for item in self if by(item)]
        elif isinstance(by, (dict, set)):
            if self._key is None:
                filtered = [item for item in self if item in by]
            else:
                filtered = [item for item in self if self._key(item) in by]
        else:
            items_and_matches = [(item, match) for item, match in zip(self, by)]
            assert len(items_and_matches) == len(self), (
                f"Filter by sequence must be the same length as the Table"
            )
            filtered = [item for item, match in items_and_matches if match]
        self.rows[:] = filtered
        if self._key is not None:
            self.ids.clear()
            self.ids.update((self._key(item), i) for i, item in enumerate(self.rows))
        return self
    
    def select(self, ids: typing.Collection) -> 'Table[T]':
        """Return a new keyed table containing rows for the given ids in id order."""
        assert self._key is not None, f"Cannot select by id from a Table with no key"
        selected = self.__class__(key=self._key)
        for key in ids:
            selected.append(self.rows[self.ids[key]])
        return selected
    
    def __getitem__(self, indices: int|slice|typing.Sequence[int]) -> 'Table[T]':
        """Return a new table by positional index, slice, or index sequence."""
        sliced = self.__class__(key=self._key)
        if isinstance(indices, slice):
            sliced.extend(self.rows[indices])
        elif isinstance(indices, int):
            sliced.append(self.rows[indices])
        else:
            for index in indices:
                sliced.append(self.rows[index])
        return sliced
    
    def slice(self, indices: int|slice|typing.Sequence[int]) -> 'Table[T]':
        """Keep rows in place by positional index, slice, or index sequence."""
        sliced = self[indices]
        self.rows[:] = sliced.rows
        if self._key is not None:
            self.ids.clear()
            self.ids.update(sliced.ids)
        return self

    def group(self, by: typing.Callable[[T], G]) -> dict[G, 'Table[T]']:
        """Group rows into keyed subtables by a grouping function."""
        groups = {}
        for item in self:
            key = by(item)
            if key not in groups:
                groups[key] = self.__class__(key=self._key)
            groups[key].append(item)
        return groups

    def sort(self, by: typing.Callable[[T], typing.Any]|typing.Iterable, reverse=False):
        """Sort rows in place by a key function or a parallel sequence of keys."""
        if not callable(by):
            items_and_keys = [(item, key) for item, key in zip(self, by)]
            assert len(items_and_keys) == len(self), f"Sort by sequence must be the same length as the Table"
            items_and_keys.sort(key=lambda x: x[1], reverse=reverse)
            self.rows[:] = [item for item, key in items_and_keys]
        else:
            self.rows.sort(key=by, reverse=reverse)
        return self
    
    def discard(self, ids: typing.Iterable[typing.Hashable]) -> 'Table[T]':
        """Remove rows by id, ignoring ids that are not present."""
        assert self._key is not None, f"Cannot discard by id from a Table with no key"
        discarded = set(ids)
        self.rows[:] = [item for item in self.rows if self._key(item) not in discarded]
        self.ids.clear()
        self.ids.update((self._key(item), i) for i, item in enumerate(self.rows))
        return self

    def remove(self, ids: typing.Iterable[typing.Hashable]) -> 'Table[T]':
        """Remove rows by id, erroring if any requested id is absent."""
        assert self._key is not None, f"Cannot remove by id from a Table with no key"
        removed = set(ids)
        missing = removed.difference(self.ids)
        assert not missing, f"Items with IDs {missing} do not exist."
        self.rows[:] = [item for item in self.rows if self._key(item) not in removed]
        self.ids.clear()
        self.ids.update((self._key(item), i) for i, item in enumerate(self.rows))
        return self

    def delete(self, indices: typing.Union[int, 'slice', typing.Sequence[int]]) -> 'Table[T]':
        """Remove rows in place by position."""
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
        if self._key is not None:
            self.ids.clear()
            self.ids.update((self._key(item), i) for i, item in enumerate(self.rows))
        return self

    def __delitem__(self, indices: typing.Union[int, 'slice', typing.Sequence[int]]):
        """Delete rows by position using `del table[...]` syntax."""
        self.delete(indices)

    def _join_index(
        self,
        other: 'Table[U]',
        against: typing.Callable[[U], typing.Hashable]|None,
    ) -> dict[typing.Hashable, list[tuple[int, U]]]:
        if against is None:
            assert other.key is not None, (
                f"Cannot join against a Table with no key without an against selector"
            )
            against = other.key
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
        """Alias for `join_left`."""
        return self.join_left(other, on, against)

    def join_inner(
        self,
        other: 'Table[U]',
        on: typing.Callable[[T], typing.Hashable],
        against: typing.Callable[[U], typing.Hashable]|None = None,
    ) -> 'Table[tuple[T, U]]':
        """Return matching row pairs only."""
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
        """Return a left join as `(left, right_or_none)` tuples."""
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
        """Return a right join as `(left_or_none, right)` tuples."""
        if against is None:
            assert other.key is not None, (
                f"Cannot join against a Table with no key without an against selector"
            )
            against = other.key
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
        """Return an outer join as `(left_or_none, right_or_none)` tuples."""
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
        """Return the cartesian product as `(left, right)` tuples."""
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
        """Render the table as a readable plain-text dump.

        Parameters
        ----------
        rows:
            Optional maximum number of rows to show.
        width:
            Maximum line width for the rendered output.
        cols:
            Optional column configuration.
            Values may be:

            - `True`: include the attribute using the same column name
            - `False`: exclude the inferred attribute
            - `str`: rename an existing attribute into a new column name
            - callable: compute a display value for the column
        cell_width:
            Minimum truncation target for columns before columns are dropped
            from the right to satisfy `width`.

        Notes
        -----
        Empty tables render a title only.
        """
        rows_ = list(self.rows)
        type_names = []
        for row in rows_:
            name = type(row).__name__
            if name not in type_names:
                type_names.append(name)
        if type_names:
            title = f"Table of {', '.join(type_names)} with {len(rows_)} rows"
        else:
            title = f"Table with {len(rows_)} rows"
        if not rows_:
            if len(title) > width:
                title = title[:max(width - 2, 0)] + ('..' if width >= 2 else '')
            return title
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
        """Print `render(...)` and return the rendered string."""
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
    print(f"{list(table.map(lambda x: x.bar[0])) = }")
    print(f"{list(table.map(lambda x: x.bar[1].capitalize())) = }")
    print(f"{list(table.map(lambda x: x.bat)) = }")

    table.display(width=30)
