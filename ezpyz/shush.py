"""
Use `shush` as a context manager to suppress stdout and stderr.
"""

from io import StringIO
import sys


class shush:
    def __init__(self):
        self.save_stdout = sys.stdout
        self.save_stderr = sys.stderr
        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()

    def __enter__(self):
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.save_stdout
        sys.stderr = self.save_stderr
