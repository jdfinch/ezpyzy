

import atexit
import ezpyzy as ez
import dataclasses as dc
import collections as col
import pathlib as pl
import typing as T


D = T.TypeVar('D')


class StoreFolder:

    _to_save = {}
    _folders = {} # need paths to be globally tracked here

    def __init__(self, name:str, load=False, save_on_exit=True):
        self.parent:StoreFolder|None = None
        self.paths:dict[str,StoreFolder|ez.Store] = {}
        path = pl.Path(name)
        self.name:str = path.name
        current = self
        for part in path.parts[:-1]:
            current.parent = StoreFolder(part)
            current = current.parent
        if load:
            self.load()
        if save_on_exit:
            StoreFolder._to_save[self.path().resolve()] = self

    def __getitem__(self, subpath:ez.filelike):
        path = ez.File(subpath).path
        current = self
        for part in path.parts:
            current = current.paths[part]
        return current

    def __truediv__(self, subpath):
        path = ez.File(subpath).path
        current = self
        for part in path.parts:
            if part not in current.paths:
                current.paths[part] = StoreFolder(part)
                current.paths[part].parent = current
            current = current.paths[part]
        return current

    def __contains__(self, subpath):
        path = ez.File(subpath).path
        current = self
        for part in path.parts:
            if part not in current.paths:
                return False
        return True

    def store(self, subpath:ez.filelike, data, format:ez.formatlike=None):
        current = self
        path = ez.File(subpath).path
        for part in path.parts[:-1]:
            if part not in current.paths:
                current.paths[part] = StoreFolder(part)
                current.paths[part].parent = current
            current = current.paths[part]
        if not isinstance(data, ez.Store):
            data = ez.Store(data,
                path=current.path()/path.parts[-1],
                format=format,
                save_on_exit=False)
        current.paths[path.parts[-1]] = data
        return data

    def __setitem__(self, subpath:ez.filelike, data):
        self.store(subpath, data)

    def save(self):
        stack = [self]
        while stack:
            current = stack.pop()
            current.path().mkdir(exist_ok=True, parents=True)
            for name, child in current.paths.items():
                if isinstance(child, StoreFolder):
                    stack.append(child)
                else:
                    child.save()

    def load(self, depth=1):
        path = self.path()
        if path.exists() and path.is_dir():
            for child in path.iterdir():
                if child.is_dir():
                    if depth > 1:
                        (self/child.name).load(depth-1)
                else:
                    self[child.name] = ez.Store(path=child, save_on_exit=False)
                    self[child.name].load()

    def path(self):
        parts = []
        current = self
        while current is not None:
            parts.append(current.name)
            current = current.parent
        return pl.Path(*reversed(parts))


def save_on_exit():
    visited = set()
    for path, store in StoreFolder._to_save.items():
        if path not in visited:
            store.save()
            visited.add(path)

atexit.register(save_on_exit)


