from __future__ import annotations

import atexit as atx
import io
import signal as sig
import pathlib as pl
import os
import datetime as dt
import weakref as wr
import ezpyzy.format

from ezpyzy.bind import bind

import typing as T

filelike: T.TypeAlias = T.Union[str, pl.Path, io.IOBase, 'File']


files: wr.WeakValueDictionary[pl.Path, 'File'] = wr.WeakValueDictionary()
_autosaving = set() # strong references for autosaved files

D = T.TypeVar('D')


class File(T.Generic[D]):

    def __new__(
        cls,
        path: filelike,
        data:D=None,
        format: ezpyzy.format.Format | type[ezpyzy.format.Format] | str = None,
        autosaving=None
    ):
        path = to_path(path)
        if path in files:
            return files[path]
        else:
            file = super().__new__(cls)
            files[path] = file
            return file

    def __init__(
        self,
        path: filelike,
        data:D=None,
        format: ezpyzy.format.formatlike= None,
        autosaving=False
    ):
        self._path: pl.Path = to_path(path)
        if not hasattr(self, 'data') or data is not None:
            self.data:D = data
        if not hasattr(self, '_format') or format is not None:
            self._format: type[ezpyzy.format.Format]|None = None
            if format is not None:
                self.format = to_format(format)
        if not hasattr(self, '_autosaving'):
            self._autosaving = autosaving
        if not hasattr(self, '_io'):
            self._io = None
        if not hasattr(self, '_sync_time'):
            self._sync_time = None

    @property
    def format(self):
        if self._format is not None:
            return self._format
        data_format = type(self.data)
        if (
            hasattr(data_format, 'is_binary') and
            hasattr(data_format, 'serialize') and
            hasattr(data_format, 'deserialize')
        ):
            return type(self.data)
        elif self._path.suffix in ezpyzy.format.formats:
            return ezpyzy.format.formats[self._path.suffix]
        else:
            return ezpyzy.format.Text

    @format.setter
    def format(self, format: ezpyzy.format.formatlike):
        self._format = to_format(format)

    @property
    def path(self):
        return self._path

    @property
    def autosaving(self):
        return self._autosaving

    @autosaving.setter
    def autosaving(self, value):
        if value:
            _autosaving.add(self)
        else:
            _autosaving.remove(self)
        self._autosaving = value

    @property
    def name(self):
        return self._path.name

    @property
    def stem(self):
        return self._path.stem

    @property
    def parent(self):
        return self._path.parent

    @property
    def suffix(self):
        return self._path.suffix

    def save(self, data=None, format: ezpyzy.format.formatlike = None):
        if data is None:
            data = self.data
        if format is None:
            format = self.format
        else:
            format = to_format(format)
        if data is not None:
            serialized = format.serialize(data)
            self.write(serialized)
        else:
            os.remove(self._path)

    def log(self, data=None, format: ezpyzy.format.formatlike = None):
        if data is None:
            data = self.data
        if format is None:
            format = self.format
        else:
            format = to_format(format)
        if data is not None:
            serialized = format.serialize(data)
            self.append(serialized)

    def load(self, format: ezpyzy.format.formatlike = None):
        if format is None:
            format = self.format
        else:
            format = to_format(format)
        if self._path.exists():
            serialized = self.read()
            data = format.deserialize(serialized)
            return data

    def pull(self, format: ezpyzy.format.formatlike = None):
        if format is not None:
            self.format = format
        file_stats = self.stats()
        if self._path.exists() and (
            self._sync_time is None or file_stats.modified_datetime > self._sync_time
        ):
            serialized = self.read()
            self.data = self.format.deserialize(serialized)
        else:
            self.data = None
        self._sync_time = dt.datetime.now()
        return self

    def push(self, data:D=None, format: ezpyzy.format.formatlike = None):
        if data is not None:
            self.data = data
        if format is not None:
            self.format = format
        if self.data is not None:
            serialized = self.format.serialize(self.data)
            self.write(serialized)
        else:
            os.remove(self._path)
        self._sync_time = dt.datetime.now()
        return self

    def commit(self):
        self._sync_time = dt.datetime.now()
        return self

    def revert(self, format: ezpyzy.format.formatlike = None):
        self._sync_time = None
        return self.pull(format)

    def init(self, data:D=None, format: ezpyzy.format.formatlike=None, autosaving=True):
        self._autosaving = autosaving
        if data is not None:
            self.data = data
        if format is not None:
            self.format = format
        file_stats = self.stats()
        if self._path.exists() and (
            self._sync_time is None or file_stats.modified_datetime > self._sync_time
        ):
            serialized = self.read()
            self.data = self.format.deserialize(serialized)
        elif self.data is not None:
            if not self.autosaving:
                self.push(self.data, format)
        else:
            raise FileNotFoundError(f"File {self._path} does not exist and no data was provided for file init.")
        self._sync_time = dt.datetime.now()
        return self

    def delete(self):
        if self._path.exists():
            os.remove(self._path)
        return self

    def write(self, serialized: str | bytes, offset=None):
        if self._io is None or self._io.closed():
            self.open()
            needed_to_open = True
        else:
            needed_to_open = False
        if offset is None:
            self._io.seek(0, io.SEEK_SET)
        else:
            self._io.seek(offset, io.SEEK_SET)
        self._io.write(serialized)
        self._io.truncate()
        head = self._io.tell()
        if needed_to_open:
            self._io.close()
            self._io = None
        return head

    def edit(self, serialized: str | bytes, offset=None):
        if self._io is None or self._io.closed():
            self.open()
            needed_to_open = True
        else:
            needed_to_open = False
        if offset is None:
            self._io.seek(0, io.SEEK_SET)
        else:
            self._io.seek(offset, io.SEEK_SET)
        self._io.write(serialized)
        head = self._io.tell()
        if needed_to_open:
            self._io.close()
            self._io = None
        return head

    def append(self, serialized: str | bytes):
        if self._io is None or self._io.closed():
            self.open()
            needed_to_open = True
        else:
            needed_to_open = False
        self._io.seek(0, io.SEEK_END)
        self._io.write(serialized)
        head = self._io.tell()
        if needed_to_open:
            self._io.close()
            self._io = None
        return head

    def read(self, offset=None, size=None) -> str | bytes:
        if self._io is None or self._io.closed():
            if self._path is None or not self._path.exists():
                raise FileNotFoundError(f"File {self._path} does not exist")
            if self.format is None:
                self.format = to_format(self._path.suffix)
            self.open()
            needed_to_open = True
        else:
            needed_to_open = False
        if offset is None:
            self._io.seek(0, io.SEEK_SET)
        else:
            self._io.seek(offset, io.SEEK_SET)
        if size is None:
            serialized = self._io.read()
        else:
            serialized = self._io.read(size)
        if needed_to_open:
            self._io.close()
            self._io = None
        return serialized

    def stats(self):
        return FileStats(self._path)

    def open(self):
        if not self._path.exists():
            os.makedirs(self._path.parent, exist_ok=True)
            self._path.touch()
        if hasattr(self._io, 'mode') and ('b' in self._io.mode != self.format.is_binary):
            self._io.close()
            self._io = None
        if self._io is None or self._io.closed():
            if self.format.is_binary:
                self._io = open(self._path, 'rb+')
            else:
                self._io = open(self._path, 'r+')

    def close(self):
        if self._io is not None:
            self._io.close()
            self._io = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return f"File({'' if self._path is None else self._path})"

    __repr__ = __str__


class FileStats:

    def __init__(self, path: filelike):
        self.path = to_path(path)
        self.exists = self.path.exists()
        self.accessed_time = None
        self.modified_time = None
        self.created_time = None
        self.size = None
        if self.exists:
            stats = os.stat(self.path)
            self.accessed_time = stats.st_atime
            self.modified_time = stats.st_mtime
            self.created_time = stats.st_ctime
            self.size = stats.st_size

    @property
    def accessed_datetime(self):
        return dt.datetime.fromtimestamp(self.accessed_time)

    @property
    def modified_datetime(self):
        return dt.datetime.fromtimestamp(self.modified_time)

    @property
    def created_datetime(self):
        return dt.datetime.fromtimestamp(self.created_time)


def to_path(path: filelike) -> pl.Path:
    if isinstance(path, pl.Path):
        return path
    elif isinstance(path, str):
        return pl.Path(path)
    elif isinstance(path, io.IOBase):
        if hasattr(path, 'name'):
            return pl.Path(path.name)
        else:
            raise ValueError(f"IOBase {path} has no name attribute")
    elif isinstance(path, File):
        return path._path
    else:
        raise TypeError(f"Cannot convert {path} to pathlib.Path")


def to_format(format: ezpyzy.format.formatlike) -> type[ezpyzy.format.Format]:
    if isinstance(format, str):
        if not format.startswith('.'):
            format = '.' + format
        return ezpyzy.format.formats[format]
    elif format is None:
        return ezpyzy.format.Text
    elif isinstance(format, type):
        return format  # noqa
    else:
        return type(format)


_already_saved_on_exit = False
def save_on_exit():
    global _already_saved_on_exit
    if not _already_saved_on_exit:
        for path, file in files.items():
            if file.autosaving:
                file.save()
        _already_saved_on_exit = True


def handle_signal(handler, signo, signal, frame):
    save_on_exit()
    sig.signal(signo, handler)
    sig.raise_signal(signo)


for signo in [
    sig.SIGHUP,
    sig.SIGINT,
    sig.SIGQUIT,
    sig.SIGABRT,
    sig.SIGTERM
]:
    sig.signal(signo, bind(handle_signal)(sig.getsignal(signo), signo))

atx.register(save_on_exit)
