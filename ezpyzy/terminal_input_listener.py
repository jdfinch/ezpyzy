"""
Unix only for now (no windows to dev/test on!)
"""

from __future__ import annotations

import sys
import termios
import atexit
from select import select


class TerminalInputListener:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_terminal = termios.tcgetattr(self.fd)
        self.new_terminal = termios.tcgetattr(self.fd)
        self.new_terminal[3] = (self.new_terminal[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_terminal)
        atexit.register(self.reset_terminal)
        self.chords = {
            '\x1b[A': 'up',
            '\x1b[C': 'right',
            '\x1b[B': 'down',
            '\x1b[D': 'left',
            '\x1b[H': 'home',
            '\x1b[F': 'end',
            '\x1b[1;5A': 'ctrl-up',
            '\x1b[1;5B': 'ctrl-down',
            '\x1b[1;5C': 'ctrl-right',
            '\x1b[1;5D': 'ctrl-left',
            '\x1b[1;2A': 'shift-up',
            '\x1b[1;2B': 'shift-down',
            '\x1b[1;2C': 'shift-right',
            '\x1b[1;2D': 'shift-left',
            '\x1b[1;2H': 'shift-home',
            '\x1b[1;2F': 'shift-end',
            '\x1b[1;5H': 'ctrl-home',
            '\x1b[1;5F': 'ctrl-end',
            '\x1b[1;6A': 'ctrl-shift-up',
            '\x1b[1;6B': 'ctrl-shift-down',
            '\x1b[1;6C': 'ctrl-shift-right',
            '\x1b[1;6D': 'ctrl-shift-left',
            '\x1b[1;6H': 'ctrl-shift-home',
            '\x1b[1;6F': 'ctrl-shift-end',
            '\x1b[3~': 'delete',
            '\x1b[Z': 'shift-tab',
            '\x1b[2~': 'insert',
            '\x1b[5~': 'page-up',
            '\x1b[6~': 'page-down',
            '\x7f': 'backspace',
            '\x1b\x7f': 'alt-backspace'
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset_terminal()

    def reset_terminal(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_terminal)

    def get_key_press(self, seconds_to_wait:int|None=None):
        if select([sys.stdin], [], [], seconds_to_wait)[0]:
            return self._handle_key_press()

    def _handle_key_press(self):
        char = sys.stdin.read(1)
        if char == '\x1b':
            candidate_chords = [chord for chord in self.chords if chord.startswith(char)]
            while True:
                read = sys.stdin.read(1)
                if read == '\n':
                    break
                char += read
                candidate_chords = [chord for chord in candidate_chords if chord.startswith(char)]
                if len(candidate_chords) <= 1:
                    break
        else:
            char = char[0] + char[1:].rstrip('\n')
        if char in self.chords:
            return self.chords[char]
        elif char.startswith('\x1b'):
            return 'alt-' + char[1:]
        elif len(char) == 1 and ord(char) < 32:
            return 'ctrl-' + chr(ord(char) + 64)
        else:
            return char


if __name__ == "__main__":
    x = input('Hello world! Give me some input:  ')
    print('You said:', x)
    with TerminalInputListener() as kb:
        while True:
            x = kb.get_key_press()
            print(x, end='  ', flush=True)
            if x == 'q':
                print()
                break
    x = input('Goodbye world! Give me some input:  ')
    print('You said:', x)