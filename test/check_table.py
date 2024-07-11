
from __future__ import annotations
import typing as T

import ezpyzy as ez
import dataclasses as dc


with ez.check('Define'):

    @dc.dataclass
    class Turn(ez.Row):
        text: ez.Col[str, Turn]
        index: ez.Col[int, Turn] = 0
        dial: ez.Col[str, Turn] = None
        doms: ez.Col[set[str], Turn] = ez.default(set)
        id: ez.Col[str, Turn] = None

    print(f'{Turn = }')
    print(f'{Turn.__cols__ = }')


with ez.check('Construct'):
    ...