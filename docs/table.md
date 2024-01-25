
# ezpyzy Table

## Import

```python
import ezpyzy as ez
import dataclasses as dc
```

## Define

```python
@dc.dataclass
class Turn(ez.Table):
    text: ez.ColStr = None
    speaker: ez.ColStr = None
    listener: ez.ColStr = None
    dialogue: ez.ColStr = None
    index: ez.ColInt = None
    id: ez.ColID = None
```

<details>
<summary>Is all this notation necessary?</summary>

Type hints like `ez.ColStr` are shorthand for `ez.Column[str] | str | None`, which is necessary to make type hinting work and for the `Table` constructor to discover the fields that should be considered columns and their types. When loading from .csv, the data is cast to the proper type based on this type annotation.

Also, `None` default values are necessary for several Table operations.

</details>

## Create

Create a Table with a single row like you would a normal object:

```python
turn = Turn("Hello my name is Sam, how are you?")

turn = Turn(
    text="Hello my name is Sam, how are you?",
    speaker="Sam"
)
```

Use `Table.of` to create a table from data:

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


Create a Table from a csv file (matches column names specified in the first csv row):
```python
turns = Turn.of('turns.csv')
```

<details>
<summary>What if more columns are specified in Table definition than are in the .csv or data passed to .of?</summary>

Columns are not created for those columns, but you can instead create them with placeholder data using `fill`:

```python
Table.of('turns.csv', fill=None)
```
</details>

## Table Summary

Display the table by printing it:

```python
print(table)
```

```text
Turn Table: 6 cols x 2 rows
text                              |speaker|dialogue|index|listener|id          
----------------------------------|-------|--------|-----|--------|------------
Hello my name is Sam, how are you?|Sam    |d1      |0    |None    |XYMv7DDKmKt6
I'm okay, you?                    |Alex   |d1      |1    |None    |Y4rzVeMHoFpZ
```

Control the display:

```python
print(turns().display(max_cell_width=10))
```

```text
Turn Table: 6 cols x 2 rows
text      |speaker|dialogue|index|listener|id        
----------|-------|--------|-----|--------|----------
Hello my..|Sam    |d1      |0    |None    |LRh2VMuQ..
I'm okay..|Alex   |d1      |1    |None    |Au6FhJUM..
```

Table rows:

```python
num_rows = len(turns)

for row in turns:
    ... # row is a Table itself,
    ... # but views exactly one row from the original table
```

Table columns:

```python
num_cols = len(turns())

for col in turns():
    ... # col is a reference to the Column object
```

Access a specific column:
```python
turn_text_col = turns.text
```

Rename columns:
```python
turns.new_name = turns.old_name

turns.a, turns.b = turns.b, turns.a  # swap names
```

Save to .csv:

```python
turns().save('table.csv')
```


## Accessing Row Data

```python
turn = Turn("Hello my name is Sam, how are you?", speaker="Sam")

text = turn.text()          # "Hello my name is Sam, how are you?"
speaker = turn.speaker()    # "Sam"
```

<details>
<summary>Wait, what?</summary>
Remember, `turn` is a table of only one row when using the normal `Turn` constructor. `turn.text` gives the text Column object. Calling a Column object returns the first item in the column. Thus, accessing cell data of single-row tables like `turn.text()` is a good pattern if you want to treat single-row tables like objects. 
</details>


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
row_with_id_a: Table = table['a'] # uses first IDColumn
rows_a_and_b: Table = table[['a', 'b']] # uses first IDColumn
```

Select rows by mask
```python
rows_above_2: Table = table[column > 2]
```

Select columns

```python
first_three_columns = table[table.column1, table.column2, table.column3]
```

## Copies and Views

Copy a Table (also detaches from origin, so the copy is NOT attached to the original table in any way.)
```python
copy = ~turns
```

A common pattern is to select out some data and mutate it, but you don't want changes reflected in the original Table data. Use `~` to copy-and-detach in this case:

```python
copy_of_some = ~turns[turns.text, turns.speaker][1:3]
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
```h


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

Grouping rows. The return is a dict where keys are the grouping keys and values are Table views.

```python
groups = table().group(table.column1) # group by column 1
```


## Column Operations

Column selection (copies data into a new column).

```python
item0: Column = column[0]
item1_3: Column = column[1:3]
item_with_id_a: Column = column['a'] # IDColumn only
items_above_2: Column = column[column > 2]
items_1_and_3: Column = column[[1, 3]]
items_a_and_b: Column = column[['a', 'b']] # IDColumn only
```

Column insertion (any iterable of the same length as the column can be used)
```python
column[3] = 'new_value'
column[1:3] = ['new_value1', 'new_value2']
column[[1, 3]] = ['new_value1', 'new_value2']
column[column > 2] = ['new_value1', 'new_value2']
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




