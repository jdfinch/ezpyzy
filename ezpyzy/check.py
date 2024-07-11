"""
Write tests using a context manager.

Alternative to method-based testing like pytest, for quick-and-dirty testing where tests are sequentially dependent.
"""

import sys
import traceback as tb
import io
import textwrap as tw
from ezpyzy.timer import Timer
import ezpyzy.ansi as ansi

class Check:
    def __init__(self, name: str, show: bool = True):
        self.name = name
        self.width = 80
        self.capture_stdout = io.StringIO()
        self.capture_stderr = io.StringIO()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.show = show
        self.timer = Timer()

    def __enter__(self):
        print('\n', ansi.bold, self.name, ansi.reset, ' ', '_' * (self.width - len(self.name) - 2), sep='')
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self.capture_stdout
        sys.stderr = self.capture_stderr
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timer.stop()
        time = self.timer.str.elapsed
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        if self.show:
            print()
            captured = self.capture_stdout.getvalue()
            if captured:
                print(tw.indent(captured, '    '))
        if exc_type is not None:
            if self.show:
                print(ansi.foreground_red, end='')
                error_message = tb.format_exc()
                print(tw.indent(error_message, '    '))
                print(ansi.reset, end='')
            print(f"  {ansi.foreground_red}✗{ansi.reset} {time}",) # (self.width - len(time) - 6) * '=')
        else:
            print(f"  {ansi.foreground_green}✓{ansi.reset} {time}",)# (self.width - len(time) - 6) * '=')
        return True

check = Check