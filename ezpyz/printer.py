

import dataclasses as dc


@dc.dataclass
class Printer:
    ...


def color(name: str = None, r: int = None, g: int = None, b: int = None):
    if name is not None:
        return NamedColor(name)
    else:
        return RGBColor(r, g, b)


@dc.dataclass
class RGBColor:
    _r: int
    _g: int
    _b: int

    @property
    def fg(self):
        return f"\033[38;2;{self._r};{self._g};{self._b}m"

    @property
    def bg(self):
        return f"\033[48;2;{self._r};{self._g};{self._b}m"

    @property
    def name(self):
        return None

    def __str__(self):
        return f"Color({self._r}, {self._g}, {self._b})"
    __repr__ = __str__


@dc.dataclass
class NamedColor:
    name: str

    def __post_init__(self):
        assert self.name in self._fg, f"Color name must be one of {list(self._fg.keys())}"

    _fg = dict(
        black='\033[30m',
        red = '\033[31m',
        green = '\033[32m',
        orange = '\033[33m',
        blue = '\033[34m',
        purple = '\033[35m',
        cyan = '\033[36m',
        gray = '\033[37m',
        darkgray = '\033[90m',
        lightred = '\033[91m',
        lightgreen = '\033[92m',
        yellow = '\033[93m',
        lightblue = '\033[94m',
        pink = '\033[95m',
        lightcyan = '\033[96m',
        white = '\033[97m'
    )
    
    _bg = dict(
        black='\033[40m',
        red='\033[41m',
        green='\033[42m',
        orange='\033[43m',
        blue='\033[44m',
        purple='\033[45m',
        cyan='\033[46m',
        gray='\033[47m',
        darkgray='\033[100m',
        lightred='\033[101m',
        lightgreen='\033[102m',
        yellow='\033[103m',
        lightblue='\033[104m',
        pink='\033[105m',
        lightcyan='\033[106m',
        white='\033[107m'
    )

    @property
    def fg(self):
        return self._fg[self.name]

    @property
    def bg(self):
        return self._bg[self.name]


    def __str__(self):
        return f"Color({self.name})"
    __repr__ = __str__

