
from __future__ import annotations

import dataclasses as dc
import ezpyzy.ansi as ansi

import threading as th
import atexit as ae
import time


@dc.dataclass
class OutputElement:
    value: str|list[tuple[float, str]]
    line: int|None
    column: int|None
    width: int|None
    height: int|None
    left: int|None
    right: int|None
    top: int|None
    bottom: int|None
    horizontal: str = 'l'
    vertical: str = 't'

    def __post_init__(self):
        if isinstance(self.value, str):
            self.value: list[tuple[float, str]] = [(1.0, self.value)]
        ...

"""
Not ready for this yet. Needs dedicated window management data structures.
"""


def printing():
    for ch in buffer: # noqa
        print(ch, end='', flush=True)
        time.sleep(0.2)

worker = th.Thread(target=printing, args=(), daemon=True)
worker.start()

def cleanup():
    worker.join()

ae.register(cleanup)


if __name__ == '__main__':
    ...