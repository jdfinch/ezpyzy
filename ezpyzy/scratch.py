
import atexit as atx
import io
import signal as sig
import pathlib as pl
import os
import datetime as dt

from ezpyzy.bind import bind

import typing as T

filelike: T.TypeAlias = T.Union[str, pl.Path, io.IOBase, 'File']

class Format(T.Protocol):
    is_binary: bool
    def serialize(obj: ...) -> str|bytes: pass
    @classmethod
    def deserialize(cls, string:str|bytes) -> T.Any: pass


formatlike = T.Union[str, Format, type[Format], None]

files: dict[pl.Path, 'File'] = {}

formats: dict[str, type[Format]] = {}


class File:

    def __new__(cls,
        path: filelike,
        data=None,
        format: Format | type[Format] | str = None,
        autosaving=None
    ):
        path = to_path(path)
        if path in files:
            return files[path]
        else:
            return super().__new__(cls)

    def __init__(self,
        path:filelike,
        data=None,
        format:Format|type[Format]|str=None,
        autosaving=None
    ):
        self._path: pl.Path = to_path(path)
        if not hasattr(self, 'data') or data is not None:
            self.data: T.Any = data
        if not hasattr(self, 'format') or format is not None:
            self.format: type[Format] = to_format(self._path.suffix if format is None else format)
        if not hasattr(self, 'autosaving') or autosaving is not None:
            self.autosaving = autosaving
        if not hasattr(self, '_io'):
            self._io = None

    @property
    def path(self):
        return self._path

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

    def save(self, data=None, format:formatlike=None):
        if data is not None:
            self.data = data
        if format is not None:
            self.format = to_format(format)
        if self.data is not None:
            serialized = self.format.serialize(self.data)
            self.write(serialized)
        else:
            os.remove(self._path)

    def log(self, data=None, format: formatlike=None):
        if data is not None:
            self.data = data
        if format is not None:
            self.format = to_format(format)
        if self.data is not None:
            serialized = self.format.serialize(self.data)
            self.append(serialized)

    def load(self, format: formatlike=None):
        if format is not None:
            self.format = to_format(format)
        if self._path.exists():
            serialized = self.read()
            self.data = self.format.deserialize(serialized)
            return self.data

    def autosave(self, data=None, format=None):
        if data is not None:
            self.data = data
        if format is not None:
            self.format = to_format(format)
        self.autosaving = True

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

def to_format(format: formatlike) -> type[Format]:
    if isinstance(format, str):
        if not format.startswith('.'):
            format = '.' + format
        return formats[format]
    elif format is None:
        return formats['']
    elif isinstance(format, type):
        return format # noqa
    else:
        return type(format)


def save_on_exit():
    for path, file in files.items():
        if file.autosaving:
            file.save()

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
