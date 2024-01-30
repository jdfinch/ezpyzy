"""
Time things with a context manager. Nice display of time elapsed.
"""

from __future__ import annotations

import time
import dataclasses


@dataclasses.dataclass
class Timer:
    start: float = None
    end: float|None = None

    def __init__(self, message=None, show=True):
        self.message = message
        self.show = show
        self.end = None
        self.display = None
        self.delta = None
        self.start = time.perf_counter()

    def __enter__(self):
        if self.show:
            print(self.message, end='... ')
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.end = time.perf_counter()
        self.delta = self.end - self.start
        self.display = format_time(self.delta)
        if self.show:
            print(self.display)
    stop=__exit__


def format_time(num_seconds):
    if num_seconds < 1:
        return f"{num_seconds * 1e3:.2f} ms"
    elif num_seconds < 60:
        return f"{num_seconds:.2f} s"
    elif num_seconds < 3600:
        minutes = num_seconds // 60
        seconds = num_seconds % 60
        return f"{int(minutes)} m, {seconds:.2f} s"
    else:
        hours = num_seconds // 3600
        remaining_seconds = num_seconds % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        return f"{int(hours)} h, {int(minutes)} m, {int(seconds)} s"




