
# Table

## Define

```python
@dc.dataclass
class Turn(Table):
    text:Column.str
    speaker:Column.str = None
    listener:Column.str = None
    dialogue:Column.str = None
    index:Column.int = None
    id:Column.ID.str = None
```

## Create

Create a Table with a single example (can be joined with other examples)

```python
turn = Turn("Hello my name is Sam, how are you?")

turn = Turn(
    text="Hello my name is Sam, how are you?",
    speaker="Sam"
)
```

Create a Table from a list of examples
```python
turns = Turn.of([
  ["Hello my name is Sam, how are you?", "Sam", "Alex", "d1", 0, None],
  ["I'm okay, you?"                    , "Alex", "Sam", "d1", 1, None]
])

turns = Turn.of([
    dict(text="Hello my name is Sam, how are you?", speaker="Sam",  dialogue="d1", index=0),
    dict(text="I'm okay, you?"                    , speaker="Alex", dialogue="d1", index=1)
])
```

Create a Table from columns
```python
turns = Turn(
    text=Column(["Hello my name is Sam, how are you?", "I'm okay, you?"]),
    speaker=Column(["Sam", "Alex"]),
    dialogue=Column(["d1", "d1"]),  
    index=Column([0, 1])
)
```

Copy a Table (also detaches from origin)
```python
copy = ~turns
```

## Table Metadata

Table name, size, and columns can be accessed by calling the table.

```python
name = turns().name
num_rows, num_cols = turns().size
columns_dict = turns().columns
origin = turns().origin
id_column = turns().id
```

Iterating over table metadata iterates over columns.
```python
for column in turns():
    print(column.name)
```

Whereas iterating over the table normally iterates over rows.
```python
for row in turns:
    print(row.text)
```

Serialization and deserialization (json-style)
```python
serialized = turns().serialize()
deserialized = Turn.deserialize(serialized)
turns().save("turns.json")
turns = Turn.load("turns.json")
```


## Attributes

```python
turn = Turn("Hello my name is Sam, how are you?", speaker="Sam")

text = turn.text()          # "Hello my name is Sam, how are you?"
speaker = turn.speaker()    # "Sam"
```

## Joins

Inner Join

```python
inner_join = table1.column1 & table2.column2
```

Left Join

```python
left_join = table1.column1 << table2.column2
```

Right Join

```python
right_join = table1.column1 >> table2.column2
```

Full Join

```python
full_join = table1.column1 | table2.column2
```

Outer Join

```python
outer_join = table1.column1 ^ table2.column2
```

Cartesian Product

```python
cartesian_product = table1 @ table2
```

Column-Wise Concatenation (one arg must be a table, not both columns, and the number of rows must be the same)

```python
concatenated = table1 - table2
```

Row-Wise Concatenation (one arg must be a table, not both columns, and the number of columns must be the same)

```python
concatenated = table1 + table2
```


## Naming

Naming rules during joins:

* table name is class name by default
* based on attribute name of column object in table attributes
* on join, the resulting table is given attributes:
  * each column in the left table takes precendence
  * `.A` and `.B` where `A` and `B` are the joined table names, if they are different and don't exist already
  * `.A`, and `.B` have sub-attributes of their columns
  * each column in the right table that doesn't already exist

In the worst case, the following attributes can be used to distinguish columns from the left and right tables:
```python
col_count_from_left = table().L.count
col_count_from_right = table().R.count
```

Columns can also be aliased using simple assignment:
```python
table.alias = table.column
```

The assignment counts as an alias if the column already exists in the table, but counts as adding a new column if it doesn't already exit.

All aliases will be transfered to joined tables using the same rules as above.

Note that unpacking can be used to shuffle column names around, such as the following name swap operation:
```python
table.column1, table.column2 = table.column2, table.column1
```

## Selecting

Selection returns a view of the origin that is selected from. Detaching (`~`) the selection view will return a copy of the selected data and remove the origin reference.

Select rows by index
```python
row0: Table = table[0]
row1_3: Table = table[1:3]
rows_1_and_3: Table = table[[1, 3]]
```

Select rows by ID
```python
row_with_id_a: Table = table['a'] # uses first DictColumn
rows_a_and_b: Table = table[['a', 'b']] # uses first DictColumn
```

Select rows by mask
```python
rows_above_2: Table = table[column > 2]
```

Select columns

```python
first_three_columns = table[table.column1, table.column2, table.column3]
```

Reorder columns (`...` is a wildcard for all other columns in their original order)
```python
reordered = table[table.column2, ..., table.column3, table.column1]
```

## Mutation

Setting attributes of a single record.
```python
record.attribute("new_value")
```

Mutating joins use assignment-style syntax with the same operators. For example, a mutating inner join would look like:
```python
table1.column1 &= table2.column2
```

Data insertion. Data must be the same length as the number of rows, and each item must be the same length as the number of columns (alternatively, a Table can be used). Like other mutation operations, this modifies the origin table. In this example, the 1st and 3rd columns of the 3rd, 4th, and 5th rows are replaced with new string data.
```python
table[3:6][table.column1, table.column3] = [
    ["new_value1", "new_value3"],
    ["new_value2", "new_value4"],
    ["new_value3", "new_value5"]
]
```

## Table-Wise Ops

Row-wise apply. If all returns are of the type...
1. Table (with the same number of columns): the result is a Table with the same number of columns, row-concatenated in order of original rows.
2. Column (of the same length): the result is a Table with all columns concatenated.
3. None: there is no result-- it is the responsibility of the apply function to mutate each row or do other useful work.
4. Any other type: the result is a Column with the length of the original table, where each element is the result of the apply function.

In the below example, note that the apply is mutating `column3` (the result of adding `column1` and `column2`), and the `.apply` call will return a column that is a copy of `column3`.
```python
table().apply(lambda row: row.column3(row.column1() + row.column2()))
```

Sorting rows. The input can be a key function, or an iterable of the same length as the table to be used as a key (such as a specific column).

```python
table().sort(lambda row: row.column1())
```

Grouping rows. The input can be a key function, or an iterable of the same length as the table to be used as a key (such as a specific column). The keys are equality-compared to determine groups. The result is a `Groups` object with the same interface as a table, but with operations applied independently to each group.

```python
table().group(table.column1)
```

To support merging groups back into a single table, a `Groups` object can be converted to a table with the `group` method with no args. This will concatenate all groups into a single table, and return a copy of the original table with the new data. Calling `.group()` on a Table instead of a Groups object just returns the original table.

```python
table().group(table.column1).apply(
  lambda group: group.count.max()
).group()
```

## Origination

Tables and Columns that are derived through the following operations have a `.origin` attribute that points to the original table:

* `&`, `<<`, `>>`, `|`, `^`, `/`, `-`, `+`, `*` (left table is origin)
* table[...]
* table.column
* Table.of(table)
* Table.of(table.column1, table.column2, ...)

Origin-sensitive operations will condition operations on the provided arguments, but use the origin table to construct the result. These include:
* Joins `&`, `<<`, `>>`, `|`, `^`, `*`
* All column `.s` operations (e.g. `.s.max()`)

A table or column can be detached from its origin with:
```python
detached = ~table
```

Detaching the origin copies the data from the original table with the origin reference removed in the copy.


## Column Operations

Column selection (copies data into a new column).

```python
item0: Column = column[0]
item1_3: Column = column[1:3]
item_with_id_a: Column = column['a'] # DictColumn only
items_above_2: Column = column[column > 2]
items_1_and_3: Column = column[[1, 3]]
items_a_and_b: Column = column[['a', 'b']] # DictColumn only
```

Column insertion (any iterable of the same length as the column can be used)
```python
column[3] = 'new_value'
column[1:3] = ['new_value1', 'new_value2']
column[[1, 3]] = ['new_value1', 'new_value2']
column[column > 2] = ['new_value1', 'new_value2']
```

Apply an arbitrary function (copying)
```python
one_up = column.map(lambda x: x + 1)
```

Apply a function to each item in the column (mutating)
```python
one_up = column.apply(lambda x: x + 1)
```

Element-wise data operations
```python
one_up = column + 1
```

Element-wise data mutation
```python
column += 1
```

Iteration over column elements.
```python
for item in column:
    print(item)
```




