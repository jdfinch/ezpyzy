
from __future__ import annotations
import typing as T
import sys
import os
import re
if os.name == 'nt' or sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
else:
    import sys
    import termios


_input_ = sys.stdin
_output_ = sys.stdout


class CursorLocation:
    def __init__(self, y, x):
        self.y = y
        self.x = x
    def __iter__(self):
        return iter((self.y, self.x))
    def __enter__(self):
        return self
    def __exit__(self, *args):
        _output_.write(cursor_to_yx(self.y, self.x))
        _output_.flush()
    restore = __exit__
    def __str__(self):
        return cursor_to_yx(self.y, self.x)
    def __repr__(self):
        return f'{self.__class__.__name__}({self.y}, {self.x})'

def cursor_get_yx():
    if sys.platform == "win32":
        OldStdinMode = ctypes.wintypes.DWORD()
        OldStdoutMode = ctypes.wintypes.DWORD()
        kernel32 = ctypes.windll.kernel32
        kernel32.GetConsoleMode(kernel32.GetStdHandle(-10), ctypes.byref(OldStdinMode))
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 0)
        kernel32.GetConsoleMode(kernel32.GetStdHandle(-11), ctypes.byref(OldStdoutMode))
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    else:
        OldStdinMode = termios.tcgetattr(_input_)
        _ = termios.tcgetattr(_input_)
        _[3] = _[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(_input_, termios.TCSAFLUSH, _)
    try:
        reply = ""
        _output_.write("\x1b[6n")
        _output_.flush()
        while not (reply := reply + sys.stdin.read(1)).endswith('R'):
            pass
        res = re.match(r".*\[(?P<y>\d*);(?P<x>\d*)R", reply)
    finally:
        if sys.platform == "win32":
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), OldStdinMode)  # noqa
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), OldStdoutMode)  # noqa
        else:
            termios.tcsetattr(_input_, termios.TCSAFLUSH, OldStdinMode)
    if res:
        return int(res.group("y")), int(res.group("x"))
    else:
        raise ValueError("Could not get cursor position.")

def cursor_save():
    return CursorLocation(*cursor_get_yx())

def screen_get_size():
    size = os.get_terminal_size(_output_.fileno())
    return size.lines, size.columns

reset = '\033[0m'
bold = '\033[1m'
faint = '\033[2m'
italic = '\033[3m'
underline = '\033[4m'
slow_blink = '\033[5m'
rapid_blink = '\033[6m'
reverse = '\033[7m'
invisible = '\033[8m'
strikethrough = '\033[9m'
foreground_black = '\033[30m'
foreground_red = '\033[31m'
foreground_green = '\033[32m'
foreground_orange = '\033[33m'
foreground_blue = '\033[34m'
foreground_purple = '\033[35m'
foreground_cyan = '\033[36m'
foreground_gray = '\033[37m'
foreground_lightblack = '\033[90m'
foreground_lightred = '\033[91m'
foreground_lightgreen = '\033[92m'
foreground_lightorange = '\033[93m'
foreground_lightblue = '\033[94m'
foreground_lightpurple = '\033[95m'
foreground_lightcyan = '\033[96m'
foreground_lightgray = '\033[97m'
foreground_default = '\033[39m'
background_black = '\033[40m'
background_red = '\033[41m'
background_green = '\033[42m'
background_orange = '\033[43m'
background_blue = '\033[44m'
background_purple = '\033[45m'
background_cyan = '\033[46m'
background_gray = '\033[47m'
background_lightblack = '\033[100m'
background_lightred = '\033[101m'
background_lightgreen = '\033[102m'
background_lightorange = '\033[103m'
background_lightblue = '\033[104m'
background_lightpurple = '\033[105m'
background_lightcyan = '\033[106m'
background_lightgray = '\033[107m'
background_default = '\033[49m'
foreground_256: T.Callable[[int], str] = '\033[38;5;{}m'.format
background_256: T.Callable[[int], str] = '\033[48;5;{}m'.format
foreground_rgb: T.Callable[[int, int, int], str] = '\033[38;2;{};{};{}m'.format  # noqa
background_rgb: T.Callable[[int, int, int], str] = '\033[48;2;{};{};{}m'.format  # noqa
linewrapping = '\033[7h'
nolinewrapping = '\033[7l'
cursor_home = '\033[H'
cursor_to_yx: T.Callable[[int, int], str] = '\033[{};{}H'.format  # noqa
cursor_up: T.Callable[[int], str] = '\033[{}A'.format
cursor_down: T.Callable[[int], str] = '\033[{}B'.format
cursor_right: T.Callable[[int], str] = '\033[{}C'.format
cursor_left: T.Callable[[int], str] = '\033[{}D'.format
cursor_downline: T.Callable[[int], str] = '\033[{}E'.format
cursor_upline: T.Callable[[int], str] = '\033[{}F'.format
cursor_to_x: T.Callable[[int], str] = '\033[{}G'.format
# cursor_save = '\033[s'
# cursor_restore = '\033[u'
erase_screen = '\033[2J'
erase_down = '\033[J'
erase_up = '\033[1J'
erase_cell = '\033[K'
erase_right = '\033[0K'
erase_left = '\033[1K'
erase_line = '\033[2K'
cursor_hide = '\033[?25l'
cursor_show = '\033[?25h'

name_to_fg_color = dict(
    black = foreground_black,
    lightblack = foreground_lightblack,
    gray = foreground_lightblack,
    grey = foreground_lightblack,
    darkgray = foreground_lightblack,
    darkgrey = foreground_lightblack,
    white = foreground_lightgray,
    lightgray = foreground_gray,
    lightgrey = foreground_gray,
    darkwhite = foreground_gray,
    offwhite = foreground_gray,
    red = foreground_red,
    darkred = foreground_red,
    lightred = foreground_lightred,
    pink = foreground_lightred,
    green = foreground_green,
    darkgreen = foreground_green,
    lightgreen = foreground_lightgreen,
    orange = foreground_orange,
    darkorange = foreground_orange,
    darkyellow = foreground_orange,
    yellow = foreground_lightorange,
    lightorange = foreground_lightorange,
    lightyellow = foreground_lightorange,
    blue = foreground_blue,
    darkblue = foreground_blue,
    lightblue = foreground_lightblue,
    purple = foreground_purple,
    violet = foreground_purple,
    darkpurple = foreground_purple,
    darkviolet = foreground_purple,
    lightpurple = foreground_lightpurple,
    lightviolet = foreground_lightpurple,
    cyan = foreground_cyan,
    darkcyan = foreground_cyan,
    teal = foreground_cyan,
    darkteal = foreground_cyan,
    lightcyan = foreground_lightcyan
)

name_to_bg_color = dict(
    black = background_black,
    lightblack = background_lightblack,
    gray = background_lightblack,
    grey = background_lightblack,
    darkgray = background_lightblack,
    darkgrey = background_lightblack,
    white = background_lightgray,
    lightgray = background_gray,
    lightgrey = background_gray,
    darkwhite = background_gray,
    offwhite = background_gray,
    red = background_red,
    darkred = background_red,
    lightred = background_lightred,
    pink = background_lightred,
    green = background_green,
    darkgreen = background_green,
    lightgreen = background_lightgreen,
    orange = background_orange,
    darkorange = background_orange,
    darkyellow = background_orange,
    yellow = background_lightorange,
    lightorange = background_lightorange,
    lightyellow = background_lightorange,
    blue = background_blue,
    darkblue = background_blue,
    lightblue = background_lightblue,
    purple = background_purple,
    violet = background_purple,
    darkpurple = background_purple,
    darkviolet = background_purple,
    lightpurple = background_lightpurple,
    lightviolet = background_lightpurple,
    cyan = background_cyan,
    darkcyan = background_cyan,
    teal = background_cyan,
    darkteal = background_cyan,
    lightcyan = background_lightcyan
)

class color:
    def __init__(self, name=None, r=None, g=None, b=None, code=None):
        if isinstance(name, str):
            self.fg = name_to_fg_color[name]
            self.bg = name_to_bg_color[name]
        elif isinstance(name, int) and r is None and code is None:
            self.fg = foreground_256(name)
            self.bg = background_256(name)
        elif isinstance(name, int) and r is not None:
            self.fg = foreground_rgb(name, r, g)
            self.bg = background_rgb(name, r, g)
        elif code is not None:
            self.fg = foreground_256(code)
            self.bg = background_256(code)
        elif r is not None and g is not None and b is not None:
            self.fg = foreground_rgb(r, g, b)
            self.bg = background_rgb(r, g, b)
        else:
            raise ValueError('Color must be initialized with a name, a code, or RGB values.')
    def __str__(self):
        return self.fg
    __repr__ = __str__


if __name__ == '__main__':
    import time
    height, width = screen_get_size()
    longline = 'really long line ' * 20
    print(longline[:width], end='\r')
    print('Hello, World!')
    print('Screen size', screen_get_size())
    print(color(55, 100, 200), end='')
    for i in range(10):
        print('-'*25)
        with cursor_save():
            print(cursor_to_yx(3, 0), end='')
            print('Screen size', screen_get_size(), end='     ')
        time.sleep(0.5)
    print(color('lightgreen'), end='')
    print(cursor_to_yx(6, 5), end='')
    time.sleep(1)
    print('Jumped')
    time.sleep(1)
    print(cursor_to_x(10), '!!!', end='')
    time.sleep(1)
    print(cursor_to_yx(20, 3), end='')
    print('Cursor location:', cursor_get_yx())
    print(color('white'), end='')
    print('Goodbye, World!')


