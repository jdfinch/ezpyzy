"""
Write tests using a context manager.

Alternative to method-based testing like pytest, for quick-and-dirty testing where tests may be sequentially dependent.
"""

from __future__ import annotations

import sys
import traceback as tb
import io
import textwrap as tw
import atexit as ae
from ezpyzy.timer import Timer
import ezpyzy.ansi as ansi

import typing as T


class Tests:
    def __init__(self, name=None):
        self.name = name or f"Test Group {len(test_groups)}"
        self.tests = []
        test_groups.append(self)

    def add(self, test: 'Test'):
        self.tests.append(test)

    def summary(self):
        passed = 0
        failed = 0
        not_run = 0
        failed_tests = []
        for test in self.tests:
            if test.result is None:
                not_run += 1
            elif test.result == 'pass':
                passed += 1
            else:
                failed += 1
                failed_tests.append(test.name)
        header = f" Summary for {self.name} ".center(80, '=')
        stats = f"  Total: {len(self.tests)}, Passed: {ansi.foreground_green}{passed}{ansi.reset}, Failed: {ansi.foreground_red}{failed}{ansi.reset}, Not Run: {ansi.foreground_gray}{not_run}{ansi.reset}\n"
        failed_list = f"\n    Failed Tests:\n{ansi.foreground_red}" + "\n".join(
            (f"      {t}" for t in failed_tests)
        ) + ansi.reset if failed_tests else ""
        return header + "\n" + failed_list + '\n\n' + stats + '\n\n'


test_groups = []
tests = Tests('All Tests')

class Test:
    def __init__(self,
        name: str,
        show: bool = True,
        raises: type[Exception] = None,
        crash: bool = False,
        group:Tests|T.Iterable[Tests] =None
    ):
        self.name = name
        self.width = 80
        self.capture_stdout = sys.stdout if show else io.StringIO()
        self.capture_stderr = sys.stderr if show else io.StringIO()
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.show = show
        self.timer = Timer()
        self.raises = raises
        self.crash = crash
        self.result = None
        self.group = tests if group is None else group
        self.group.add(self)

    def __enter__(self):
        print(ansi.bold, self.name, ansi.reset, ' ', '_' * (self.width - len(self.name) - 2), sep='')
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
        if (
            self.raises is None and exc_type is None
            or isinstance(self.raises, type)
            and isinstance(exc_type, type)
            and issubclass(exc_type, self.raises)
        ):
            print(f"  {ansi.foreground_green}✓{ansi.reset} {time}\n", )  # (self.width - len(time_to_wait_s) - 6) * '=')
            self.result = 'pass'
        elif self.raises is not None and (not isinstance(exc_type, type) or not issubclass(exc_type, self.raises)):
            if self.show:
                print(ansi.foreground_red, end='')
                error_message = f"Expected {self.raises.__name__} to raise on test {self.name}, but got {exc_type} instead."
                print(error_message, end='')
                print(ansi.reset, end='\n')
            print(f"  {ansi.foreground_red}✗{ansi.reset} {time}\n",)
        else:
            if self.show:
                print(ansi.foreground_red, end='')
                error_message = tb.format_exc()
                print(error_message, end='')
                print(ansi.reset, end='')
            print(f"  {ansi.foreground_red}✗{ansi.reset} {time}\n",) # (self.width - len(time_to_wait_s) - 6) * '=')
            self.result = exc_type
        return True if not self.crash else bool(self.result == 'pass')

test = Test


def summarize_tests():
    for test_group in test_groups:
        if test_group.tests:
            print(test_group.summary())

ae.register(summarize_tests)