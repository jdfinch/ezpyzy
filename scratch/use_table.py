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

@tabular
class Turn(tab.Tabular):
    id: tab.Col[str] = None
    text: tab.Col[str] = None
    dialogue: tab.Col[str] = None
    index: tab.Col[int] = None



turn = Turn(
    id='abc',
    text='Hello',
    dialogue='d1',
    index=1
)

turns = Turn.s()
for turn in turns:
    turn.text = 'Hello'

for element in turns.text:
    print(element)

meta = turns()






