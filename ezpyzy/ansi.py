
from __future__ import annotations
import typing as T
import sys
import re
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
else:
    import termios


_input_ = sys.stdin
_output_ = sys.stdout


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
        _ = ""
        _output_.write("\x1b[6n")
        _output_.flush()
        while not (_ := _ + _input_.read(1)).endswith('R'):
            True
        res = re.match(r".*\[(?P<y>\d*);(?P<x>\d*)R", _)
    finally:
        if sys.platform == "win32":
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), OldStdinMode)  # noqa
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), OldStdoutMode)  # noqa
        else:
            termios.tcsetattr(_input_, termios.TCSAFLUSH, OldStdinMode)
    if res:
        return int(res.group("y")), int(res.group("x"))
    else:
        return None, None

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
foreground_white = '\033[37m'
foreground_lightblack = '\033[90m'
foreground_lightred = '\033[91m'
foreground_lightgreen = '\033[92m'
foreground_lightorange = '\033[93m'
foreground_lightblue = '\033[94m'
foreground_lightpurple = '\033[95m'
foreground_lightcyan = '\033[96m'
foreground_lightwhite = '\033[97m'
foreground_default = '\033[39m'
background_black = '\033[40m'
background_red = '\033[41m'
background_green = '\033[42m'
background_orange = '\033[43m'
background_blue = '\033[44m'
background_purple = '\033[45m'
background_cyan = '\033[46m'
background_white = '\033[47m'
background_lightblack = '\033[100m'
background_lightred = '\033[101m'
background_lightgreen = '\033[102m'
background_lightorange = '\033[103m'
background_lightblue = '\033[104m'
background_lightpurple = '\033[105m'
background_lightcyan = '\033[106m'
background_lightwhite = '\033[107m'
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
cursor_save = '\033[s'
cursor_restore = '\033[u'
erase_screen = '\033[2J'
erase_down = '\033[J'
erase_up = '\033[1J'
erase_cell = '\033[K'
erase_right = '\033[0K'
erase_left = '\033[1K'
erase_line = '\033[2K'
cursor_hide = '\033[?25l'
cursor_show = '\033[?25h'



if __name__ == '__main__':
    import time
    print('Hello, World!')
    print(foreground_rgb(55, 100, 200), end='')
    for i in range(10):
        print('-'*10)
        time.sleep(0.5)
    print(cursor_to_yx(6, 5), end='')
    time.sleep(1)
    print('Jumped')
    time.sleep(1)
    print('!!!', end='')
    time.sleep(1)
    print(cursor_to_yx(20, 3), end='')
    print('Cursor location:', cursor_get_yx())
    print('Goodbye, World!')


