
import dataclasses as dc
import typing as T

default = object()


@dc.dataclass
class WindowAxis: 
    size: int|None = None
    """the recommended len of the axis span"""
    min: int|None = None
    """the absolute min len of the axis span"""
    max: int|None = None
    """the absolute max len of the axis span"""
    fill: bool = True
    """whether the axis span should grow to fill its container"""
    pad: int = 0
    """the padding space of contents in this axis span from its boundaries"""
    space: int = 0
    """the padding spac between content items in this axis span"""
    align: T.Literal['L', 'C', 'R', 'T', 'M', 'B'] = 'L'
    """the positional alignment"""
    offset: int = 0
    """the positional offset of the axis span (based on align)"""
    reverse: bool = False
    """???"""
    floor: int = 0
    """the calculated minimum length of the axis span, accounting for its items"""
    len: int = 0
    """the final calculated length of the axis span"""
    pos: int = 0
    """the final calculated position of the axis span from the top/left"""
    window: 'Window' = None
    """window owning this axis"""

    def update(self, 
        size: int|None = default,
        min: int|None = default,
        max: int|None = default,
        fill: bool = default,
        pad: int = default,
        space: int = default,
        align: T.Literal['L', 'C', 'R', 'T', 'M', 'B'] = default,
        offset: int = default,
        reverse: bool = default,
    ):
        if size is not default:
            self.size = size
        if min is not default:
            self.min = min
        if max is not default:
            self.max = max
        if fill is not default:
            self.fill = fill
        if pad is not default:
            self.pad = pad
        if space is not default:
            self.space = space
        if align is not default:
            self.align = align
        if offset is not default:
            self.offset = offset
        if reverse is not default:
            self.reverse = reverse
        return self

    def fill_along_axis(self, items: list['WindowAxis']):
        """Calculate the floor and len this win axis needs to fit all the given items (bottom-up)"""
        self.floor = self.min or 0
        if items: 
            floor = self.pad*2 + self.space*(len(items)-1) + sum(x.floor for x in items)
            if floor > self.floor: self.floor = floor
            if self.size is not None:
                self.len = self.size
            else:
                self.len = self.pad*2 + self.space*(len(items)-1) + sum(x.len for x in items)
        else:
            self.len = self.size or 0
        if self.max is not None:
            if self.len > self.max:
                self.len = self.max
            if self.floor > self.max:
                self.floor = self.max
        if self.len < self.floor:
            self.len = self.floor

    def fill_cross_axis(self, items: list['WindowAxis']):
        """Calculate the floor and len this win axis needs to fit all the given items (bottom-up)"""
        self.floor = self.min or 0
        if items:
            floor = self.pad*2 + max(x.floor for x in items)
            if floor > self.floor: self.floor = floor
            if self.size is not None:
                self.len = self.size
            else:
                self.len = self.pad*2 + max(x.size for x in items)
        else:
            self.len = self.size or 0
        if self.max is not None:
            if self.len > self.max:
                self.len = self.max
            if self.floor > self.max:
                self.floor = self.max
        if self.len < self.floor:
            self.len = self.floor

    def fit_along_axis(self, items):
        if items:
            spacing = self.pad*2 + self.space*(len(items)-1)
            size = spacing + sum(x.len for x in items)
            empty = self.len - size
            if empty > 0:
                while growers:=[x for x in items if x.fill and (x.max is None or x.len < x.max)]:
                    smallest_size = min(x.len for x in growers)
                    smallest = [x for x in growers if x.len == smallest_size]
                    empty_per_smallest = empty // len(smallest)
                    empty_remainder = empty % len(smallest)
                    growth_to_full = empty_per_smallest + bool(empty_remainder)
                    growths = [growth_to_full]
                    growths.extend(x.len - smallest_size for x in growers if x.len != smallest_size)
                    growths.extend(x.max - smallest_size for x in smallest if x.max is not None)
                    min_growth = min(growths)
                    if min_growth == growth_to_full:
                        for i, x in enumerate(smallest):
                            x.len += min_growth - (i < empty_remainder)
                        break
                    else:
                        for x in smallest:
                            x.len += min_growth
                    size = spacing + sum(x.len for x in items)
                    empty = self.len - size
            elif empty < 0:
                overflow = -empty
                while shrinkers:=[x for x in items if x.len > x.floor]:
                    largest_size = max(x.len for x in shrinkers)
                    largest = [x for x in shrinkers if x.len == largest_size]
                    overflow_per_largest = overflow // len(largest)
                    overflow_remainder = overflow % len(largest)
                    shrink_to_fit = overflow_per_largest + bool(overflow_remainder)
                    shrinks = [shrink_to_fit]
                    shrinks.extend(largest_size - x.len for x in shrinkers if x.len != largest_size)
                    shrinks.extend(largest_size - x.floor for x in largest if x.floor)
                    min_shrink = min(shrinks)
                    if min_shrink == shrink_to_fit:
                        for i, x in enumerate(largest):
                            x.len -= min_shrink - (i < overflow_remainder)
                        break
                    else:
                        for x in largest:
                            x.len -= min_shrink
                    size = spacing + sum(x.len for x in items)
                    overflow = size - self.len

    def fit_cross_axis(self, items):
        if items:
            size = self.len - self.pad*2
            for item in items:
                if item.fill and (item.max is None or item.max >= size):
                    item.len = size
                elif item.len > size and item.floor <= size:
                    item.len = size
                elif item.floor > size:
                    item.len = item.floor

    def position_along_axis(self, items):
        if not items:
            return
        if self.reverse:
                items = reversed(items)
        if self.align in 'TL':
            p = self.pos + self.pad
            for item in items:
                item.pos = p + item.offset
                p += item.len + self.space
        elif self.align in 'MC':
            s = sum(item.len for item in items) + self.space*(len(items)-1)
            p = self.pos + (self.len - s) // 2
            for item in items:
                item.pos = p + item.offset
                p += item.len + self.space
        elif self.align in 'BR':
            p = self.pos + self.len - self.pad
            for item in items:
                p -= item.len
                item.pos = p + item.offset
                p -= self.space
        else:
            raise ValueError(f'Invalid alignment code {self.align}')

    def position_cross_axis(self, items):
        if not items:
            return
        if self.align in 'TL':
            p = self.pos + self.pad
            for item in items:
                item.pos = p + item.offset
        elif self.align in 'MC':
            for item in items:
                item.pos = self.pos + (self.len - item.len) // 2 + item.offset
        elif self.align in 'BR':
            p = self.pos + self.len - self.pad
            for item in items:
                item.pos = p - item.len + item.offset
        else:
            raise ValueError(f'Invalid alignment code {self.align}')

    def position_floating(self, items):
        if not items:
            return
        for item in items:
            if isinstance(item.offset, float):
                item.pos = self.pos + self.pad + (item.offset * self.len)
            else:
                item.pos = self.pos + self.pad + item.offset


W = T.TypeVar('W')

class Window(T.Generic[W]):
    def __init__(self,
        size: tuple[int, int] = (None, None),
        min: tuple[int|None, int|None] = (None, None),
        max: tuple[int|None, int|None] = (None, None),
        fill: bool|tuple[bool, bool] = (True, True),
        pad: tuple[int, int] = (0, 0),
        space: int = 0,
        align: T.Literal['TL', 'TC', 'TR', 'ML', 'MC', 'MR', 'BL', 'BC', 'BR'] = 'TL',
        offset: tuple[int, int] = 0,
        reverse: bool = False,
        axis: T.Literal['X', 'Y', 'F'] = 'F',
        panes: T.Iterable['Window'] = None,
        window: 'Window' = None
    ):
        self._window: Window|None = window
        self._panes: list[Window] = []
        self.view: W|None = None
        self.axis = axis
        self.x: WindowAxis = WindowAxis()
        self.y: WindowAxis = WindowAxis()
        self.x.align, self.y.align = align
        self.x.size, self.y.size = size
        self.x.min, self.y.min = min
        self.x.max, self.y.max = max
        if isinstance(fill, bool):
            self.x.fill, self.y.fill = fill, fill
        else:
            self.x.fill, self.y.fill = fill
        self.x.pad, self.y.pad = pad
        self.x.space, self.y.space = space, space
        self.x.offset, self.y.offset = offset
        self.x.reverse, self.y.reverse = reverse, reverse
        for pane in self._panes:
            self.insert(pane)
    
    @property
    def window(self) -> 'Window':
        return self._window
    
    @window.setter
    def window(self, window: 'Window'|None):
        self._window._panes.remove(self)
        self._window = window
        if window is not None:
            self._window._panes.append(self)

    def __iter__(self):
        return iter(self.panes)
    
    def insert(self, pane: 'Window', index=-1):
        if pane._window is not None:
            pane._window._panes.remove(pane)
            pane._window = self
        if index == -1:
            self._panes.append(pane)
        else:
            self._panes.insert(index, pane)

    def update(self,
        size: tuple[int, int] = default,
        min: tuple[int|None, int|None] = default,
        max: tuple[int|None, int|None] = default,
        fill: bool|tuple[bool, bool] = default,
        pad: tuple[int, int] = default,
        space: int = default,
        align: T.Literal[
            'TL', 'TC', 'TR', 'ML', 'MC', 'MR', 'BL', 'BC', 'BR'
        ] = default,
        offset: tuple[int, int] = default,
        reverse: bool = default,
        axis: T.Literal['X', 'Y', 'F'] = default,
        panes: T.Iterable['Window'] = default
    ):
        if axis is not default:
            self.axis = axis
        if align is not default:
            self.x.align, self.y.align = align
        if size is not default:
            self.x.size, self.y.size = size
        if min is not default:
            self.x.min, self.y.min = min
        if max is not default:
            self.x.max, self.y.max = max
        if isinstance(fill, bool):
            self.x.fill, self.y.fill = fill, fill
        elif fill is not default:
            self.x.fill, self.y.fill = fill
        if pad is not default:
            self.x.pad, self.y.pad = pad
        if space is not default:
            self.x.space, self.y.space = space, space
        if offset is not default:
            self.x.offset, self.y.offset = offset
        if reverse is not default:
            self.x.reverse, self.y.reverse = reverse, reverse
        if panes is not default:
            self._panes.clear()
            self._panes.extend(panes)
        return self

    def traverse_top_down(self):
        yield self
        for item in self._panes:
            yield from item.traverse_top_down()

    def traverse_bottom_up(self):
        for item in reversed(self._panes):
            yield from item.traverse_bottom_up()
        yield self

    def calculate_x_sizes(self):
        for window in self.traverse_bottom_up():
            if window.axis == 'X':
                window.x.fill_along_axis([pane.x for pane in window._panes])
            elif window.axis == 'Y':
                window.x.fill_cross_axis([pane.x for pane in window._panes])
            else:
                window.x.fill_cross_axis([pane.x for pane in window._panes])
        for window in self.traverse_top_down():
            if window.axis == 'X':
                window.x.fit_along_axis([pane.x for pane in window._panes])
            elif window.axis == 'Y':
                window.x.fit_cross_axis([pane.x for pane in window._panes])
    
    def calculate_y_sizes(self):
        for window in self.traverse_bottom_up():
            if window.axis == 'Y':
                window.y.fill_along_axis([pane.y for pane in window._panes])
            elif window.axis == 'X':
                window.y.fill_cross_axis([pane.y for pane in window._panes])
            else:
                window.y.fill_cross_axis([pane.y for pane in window._panes])
        for window in self.traverse_top_down():
            if window.axis == 'Y':
                window.y.fit_along_axis([pane.y for pane in window._panes])
            elif window.axis == 'X':
                window.y.fit_cross_axis([pane.y for pane in window._panes])
    
    def calculate_positions(self):
        for window in self.traverse_top_down():
            if window.axis == 'X':
                window.x.position_along_axis([pane.x for pane in window._panes])
                window.y.position_cross_axis([pane.y for pane in window._panes])
            elif window.axis == 'Y':
                window.x.position_cross_axis([pane.x for pane in window._panes])
                window.y.position_along_axis([pane.y for pane in window._panes])
            else:
                window.x.position_floating([pane.x for pane in window._panes])
                window.y.position_floating([pane.y for pane in window._panes])

    @property
    def size(self):
        return self.x.len, self.y.len
    
    @size.setter
    def size(self, wh: int|tuple[int, int]):
        if isinstance(wh, int):
            self.x.size, self.y.size = wh, wh
        else:
            self.x.size, self.y.size = wh

    @property
    def pos(self):
        return self.x.pos, self.y.pos
    
    @pos.setter
    def pos(self, xy: tuple[int, int]):
        self.x.offset, self.y.offset = xy

    @property
    def pad(self):
        return self.x.pad, self.y.pad
    
    @pad.setter
    def pad(self, xy: int|tuple[int, int]):
        if isinstance(xy, int):
            self.x.pad, self.y.pad = xy, xy
        else:
            self.x.pad, self.y.pad = xy

    @property
    def space(self):
        if self.axis == 'X':
            return self.x.space
        elif self.axis == 'Y':
            return self.y.space
        else:
            return None
        
    @space.setter
    def space(self, space):
        if self.axis == 'X':
            self.x.space = space
        elif self.axis == 'Y':
            self.y.space = space
        else:
            self.x.space, self.y.space = space, space

    @property
    def reverse(self):
        if self.axis == 'X':
            return self.x.reverse
        elif self.axis == 'Y':
            return self.y.reverse
        else:
            return any(self.x.reverse, self.y.reverse)
        
    @reverse.setter
    def reverse(self, reverse):
        if self.axis == 'X':
            self.x.reverse = reverse
        elif self.axis == 'Y':
            self.y.reverse = reverse
        else:
            self.x.reverse, self.y.reverse = reverse, reverse

    @property
    def fill(self):
        return any(self.x.fill, self.y.fill)
    
    @fill.setter
    def fill(self, fill: bool|tuple[bool, bool]):
        if isinstance(fill, bool):
            self.x.fill, self.y.fill = fill, fill
        else:
            self.x.fill, self.y.fill = fill

    @property
    def min(self):
        return self.x.floor, self.y.floor
    
    @min.setter
    def min(self, min: int|tuple[int, int]):
        if isinstance(min, int):
            self.x.min, self.y.min = min, min
        else:
            self.x.min, self.y.min = min

    @property
    def max(self):
        return self.x.max, self.y.max
    
    @max.setter
    def max(self, max: int|tuple[int, int]):
        if isinstance(max, int):
            self.x.max, self.y.max = max, max
        else:
            self.x.max, self.y.max = max


    



    


    
    
