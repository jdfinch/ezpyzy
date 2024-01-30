
import ezpyzy as ez
import random as rng
import itertools as it

value = ' This is a test string. It has multiple sentences to represent nontrivial data.'

num_cols = 10
num_rows = 10**7
num_groups = num_rows // 10**2

print(f'Performance test with {num_groups} groups, {num_cols} columns, and {num_rows} rows.', '\n')

with ez.Timer('Creating data'):
    data = [
        [x for _ in range(num_cols)]
        for x, _ in zip(it.cycle(ez.digital_iteration(num_groups)), range(num_rows))
    ]

with ez.Timer('Creating table'):
    table = ez.Table.of(data)
assert table().size == (num_rows, num_cols)

with ez.Timer('Creating random selection'):
    selection = [rng.randint(0, len(table)-1) for _ in range(len(table))]

with ez.Timer('Performing selection on table'):
    selected = table[selection]
assert len(selected) == len(selection)

with ez.Timer('Performing selection on table view'):
    view_select = selected[selection]
assert len(view_select) == len(selection)

with ez.Timer('Copying view'):
    copied = ~selected
assert len(copied) == len(selected)

with ez.Timer('Selecting from copied view'):
    copy_select = copied[selection]
assert len(copy_select) == len(selection)

with ez.Timer('Iterating over table columns'):
    list(zip(table.A, table.B, table.C))

with ez.Timer('Iterating over selected columns'):
    list(zip(selected.A, selected.B, selected.C))

with ez.Timer('Iterating over view_select columns'):
    list(zip(view_select.A, view_select.B, view_select.C))

with ez.Timer('Grouping table'):
    groups = table().group(table.A)
assert len(groups) == num_groups

with ez.Timer("Iterating over groups' columns"):
    for key, group in groups.items():
        list(zip(group.A, group.B, group.C))
