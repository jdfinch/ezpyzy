"""
Write tests using a context manager.

Alternative to method-based testing like pytest, for quick-and-dirty testing where tests are sequentially dependent.
"""


import sys
import traceback as tb
import io
import textwrap as tw
from ezpyzy.timer import Timer


class Check:
    def __init__(self, name: str, show: bool = True):
        self.name = name
        self.width = 80
        self.capture = io.StringIO()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.show = show
        self.timer = Timer()

    def __enter__(self):
        print(self.name, '_' * (self.width - len(self.name) - 2))
        if not self.show:
            self.stdout = sys.stdout
            self.stderr = sys.stderr
            sys.stdout = self.capture
            sys.stderr = self.capture
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timer.stop()
        time = self.timer.display
        if not self.show:
            sys.stdout = self.stdout
            sys.stderr = self.stderr
        if exc_type is not None:
            if not self.show:
                captured = self.capture.getvalue()
                if captured:
                    print(tw.indent(captured, '    '))
            print(f"\033[91m", end='')
            tb.print_exc(file=sys.stdout)
            print(f"\033[0m", end='')
            print(f"  \033[91m✗\033[0m {time}", (self.width - len(time) - 6) * '=')
        else:
            print(f"  \033[92m✓\033[0m {time}", (self.width - len(time) - 6) * '=')
        return True

check = Check