from __future__ import annotations
import scratch.table as tab
import dataclasses as dc
from dataclasses import dataclass as tabular; vars().update(tabular=tab.tabular)
from ezpyzy import settings


'''
- sorted
- link
    - reflected
- required
    - dependent
    - unique
        - key
            - id             
'''

Column = ...

class MyDescriptor:
    def __init__(self, name):
        self.name = name
    def __set__(self, instance, value):
        for table in instance.__tables__:
            column = table()[self.name]
            column.__validate_set((instance.__dict__[self.name],), (value,))


@tabular
class Turn(tab.Tabular):
    id: tab.Col[str] = None
    text: tab.Col[str] = None
    dialogue: tab.Col[str] = None
    index: tab.Col[int] = None

    def __post_init__(self):
        self.id = 'blah'



turn = Turn(
    id='abc',
    text='Hello',
    dialogue='d1',
    index=1
)

a = Turn.s()
a += Turn(id='abc', index=3)
a += Turn(id='def', index=4)

b = Turn.s()
b += Turn(id='blah', index=3)
b += Turn(id='xyz', index=4)

my_turn = a[1]

b += my_turn # to copy, or to reference?
my_turn.id = 'xyz' # should raise error, xyz already exists as an id in the table (if reference)

my_turn.id = 'abc' # should raise error, abc already exists as an id in the table

for element in a.text:
    print(element)

meta = a()




