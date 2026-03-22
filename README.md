# ezpyzy

A tiny, friendly Python utility library with a lightweight row-oriented table type.

The current headline feature is `ezpyzy.table.Table`, which provides:

- optional id-based indexing
- positional and id-based selection APIs
- in-place filtering, slicing, sorting, and deletion
- tuple-based joins
- readable plain-text rendering for inspection and debugging

## Install

```bash
pip install ezpyzy
```

For development:

```bash
pip install -e ".[dev]"
pytest
```

## Table

`Table` stores rows in insertion order and can optionally maintain an id index.

- `table.rows` is the backing list of row objects
- `table.ids` is either `None` or a `{id: index}` mapping
- `table.key` is the callable used to compute ids

Basic example:

```python
from dataclasses import dataclass

from ezpyzy.table import Table


@dataclass
class User:
    id: int
    name: str
    team_id: int


users = Table(
    [
        User(1, "Ava", 10),
        User(2, "Bo", 20),
        User(3, "Cy", 10),
    ],
    key=lambda user: user.id,
)

print(users.ids)   # {1: 0, 2: 1, 3: 2}
print(users.get(2))
```

### Construction and ids

```python
table = Table(rows)                           # unkeyed
table = Table(rows, key=lambda row: row.id)  # keyed

table.key = lambda row: row.id               # build ids from existing rows
table.key = None                             # drop id indexing
```

Keyed tables enable:

- `get(id)` / `try_get(id)`
- `keys()` / `items()` / `has(id)`
- `select(ids)`
- `discard(ids)` / `remove(ids)`
- default right-side join matching when `against` is omitted

### Adding rows

```python
table.add(row)        # append unless the id is already present
table.insert(row, 3)  # insert at an index; duplicate ids error
table.append(row)     # append; duplicate ids error
table.extend(rows)    # append many; duplicate ids error
table.update(rows)    # append many; duplicate ids are ignored
```

Table utilities:

```python
copy = table.copy()                   # shallow copy, preserves key
combined = Table(table, more_rows)    # non-mutating concatenation
table.clear()                         # clear in place
```

### Mapping and lookup

Projection methods return new tables:

```python
names = users.map(lambda user: user.name)
team_names = users.try_map(lambda user: user.team.name)  # None on missing path
```

Single-row id lookup is separate:

```python
user = users.get(1)       # raises KeyError if missing
maybe = users.try_get(5)  # returns None if missing

print(list(users.keys()))
print(list(users.items()))
print(users.has(2))
```

### Filtering and selection

Mutating filters:

```python
users.filter(lambda user: user.team_id == 10)
users.filter([True, False, True])
users.filter({1, 3})   # keyed table: keep ids 1 and 3
```

Non-mutating id selection:

```python
subset = users.select([3, 1])  # preserves requested id order
```

Positional selection:

```python
subset = users[1:3]     # new table
subset = users[[2, 0]]  # new table in requested order

users.slice([2, 0])     # mutate in place
```

### Grouping and sorting

```python
groups = users.group(lambda user: user.team_id)
team_10 = groups[10]

users.sort(lambda user: user.name)
users.sort([3, 1, 2])   # sort by a parallel sequence of sort keys
```

### Deleting rows

Id-based deletion:

```python
users.discard([99, 100])  # ignore missing ids
users.remove([1, 2])      # error if any id is missing
```

Positional deletion:

```python
users.delete(0)
users.delete(slice(1, 3))
users.delete([4, 2, 0])

del users[[3, 1]]
```

### Joins

Joins return tuple rows rather than merged objects:

```python
teams = Table(team_rows, key=lambda team: team.id)
joined = users.join(teams, lambda user: user.team_id)  # left join

for user, team in joined:
    print(user.name, team.name if team else None)
```

Available join forms:

- `join(...)` / `join_left(...)`
- `join_inner(...)`
- `join_right(...)`
- `join_outer(...)`
- `join_cartesian(...)`

If `against` is omitted, the right table must be keyed and its `key`
is used automatically.

### Rendering

`render()` is intended for inspection and debugging:

```python
print(users.render())
print(users.render(rows=5, width=80))
print(users.render(cols={
    "identifier": "id",
    "name": True,
    "team": lambda user: user.team_id,
}))
```

Column configuration supports:

- `True`: include an attribute under the same name
- `False`: exclude an inferred attribute
- `str`: rename an attribute into a new display column
- callable: compute a display value

Empty tables render a title only:

```text
Table with 0 rows
```

## API summary

Public `Table` methods:

- `add`, `insert`, `append`, `extend`, `update`
- `copy`, `clear`
- `map`, `try_map`, `get`, `try_get`
- `keys`, `items`, `has`
- `filter`, `select`, `slice`, `group`, `sort`
- `discard`, `remove`, `delete`
- `join`, `join_left`, `join_inner`, `join_right`, `join_outer`, `join_cartesian`
- `render`, `display`

## Development and release

1. Bump the version in `pyproject.toml`.
2. Build: `python -m build` or `hatch build`.
3. Upload: `twine upload dist/*`.
