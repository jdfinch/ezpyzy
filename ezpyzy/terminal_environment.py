"""
Unix only for now
"""

from __future__ import annotations

import sys
import os
import termios
import atexit
import ezpyzy.ansi as ansi
from select import select
import re

yx_pattern = re.compile(r'\x1b\[(\d+);(\d+)R')


class TerminalEnvironment:
    def __init__(self, input=None, output=None, error=None):
        if input is None:
            input = sys.stdin
        if output is None:
            output = sys.stdout
        if error is None:
            error = sys.stderr
        self._input = input
        self._output = output
        self._error = error
        self.old_terminal_settings = termios.tcgetattr(self._input.fileno())
        self.new_terminal_settings = termios.tcgetattr(self._input.fileno())
        self.new_terminal_settings[3] = (
            self.new_terminal_settings[3] & ~termios.ICANON & ~termios.ECHO)
        self.new_terminal_settings[6][termios.VMIN] = 0
        self.new_terminal_settings[6][termios.VTIME] = 0
        termios.tcsetattr(self._input.fileno(), termios.TCSAFLUSH, self.new_terminal_settings)
        self._output.write(ansi.enable_mouse_clicks + ansi.enable_mouse_sgr)
        self._output.flush()
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
            '\x1b\x7f': 'alt-backspace',
            '\x1b[<': 'mouse',
        }
        self.mouse_buttons = {
            0: 'left',
            1: 'middle',
            2: 'right',
            68: 'scroll-up',
            69: 'scroll-down',
            32: 'drag',
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        termios.tcsetattr(self._input.fileno(), termios.TCSAFLUSH, self.old_terminal_settings)
        self._output.write(ansi.disable_mouse_clicks + ansi.disable_mouse_sgr)

    def output(self, *args, **kwargs):
        print(*args, **kwargs, file=self._output)

    def input(self, seconds_to_wait: int | None=None):
        if select([sys.stdin], [], [], seconds_to_wait)[0]:
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
            return self._handle_input(char)

    def _handle_input(self, char):
        if char == '\x1b[<':
            while char[-1] not in 'mM':
                char += sys.stdin.read(1)
            parts = char[3:-1].split(';')
            button = self.mouse_buttons.get(int(parts[0]), 'unknown')
            x = parts[1]
            y = parts[2]
            if button in ('left', 'middle', 'right'):
                action = "press" if char[-1] == 'M' else "release"
                return f'mouse-{button}-{action}-{y}-{x}'
            else:
                return f'mouse-{button}-{y}-{x}'
        elif char in self.chords:
            return self.chords[char]
        elif char.startswith('\x1b'):
            return 'alt-' + char[1:]
        elif len(char) == 1 and ord(char) < 32:
            return 'ctrl-' + chr(ord(char) + 64)
        else:
            return char

    def cursor_yx(self):
        self._output.write(ansi.cursor_get_yx)
        self._output.flush()
        reply = ''
        while not reply.endswith('R'):
            reply += self._input.read(1)
        span = yx_pattern.search(reply)
        if span:
            y, x = span.groups()
            start, end = span.span()
            if start != 0:
                self._handle_input(reply[:start])
            return int(y)-1, int(x)-1
        raise ValueError(f'Could not parse cursor location')

    def cursor_to_yx(self, y:int, x:int):
        self._output.write(ansi.cursor_to_yx(y, x))
        self._output.flush()

    def screen_hw(self):
        w, h = os.get_terminal_size(self._input.fileno())
        return h, w


program_original_terminal_settings = termios.tcgetattr(sys.stdin.fileno())

def reset_original_terminal():
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, program_original_terminal_settings)
    sys.stdout.write(ansi.disable_mouse_clicks+ansi.disable_mouse_sgr)
    sys.stdout.flush()

atexit.register(reset_original_terminal)


if __name__ == "__main__":
    with TerminalEnvironment() as kb:
        while True:
            x = kb.input()
            kb.output(x, end='  ', flush=True)
            if x == 'q':
                kb.output()
                break
            y, x = kb.cursor_yx()
            h, w = kb.screen_hw()
            kb.output(f'Cursor at y: {y}, x: {x}', f'Screen size: {h}x{w}')
        kb.cursor_to_yx(10, 0)
        kb.output(ansi.bold, ansi.foreground_orange, ansi.background_black, 'Goodbye world!')
    x = input('Goodbye world! Give me some input:  ')
    print(ansi.color(25, 150, 200), 'You said:', x)