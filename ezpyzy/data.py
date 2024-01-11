import dataclasses
import abc
import json
import csv
import pickle
import io
import typing as T

import ezpyzy
from ezpyzy.file import filelike, formatlike, File
from ezpyzy.cache import Cache


C = T.TypeVar('C')

class DataMeta(abc.ABCMeta):
    formats = File.formats
    extensions = None

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        extensions = getattr(cls, 'extensions', None)
        super_extensions = getattr(super(cls, cls), 'extensions', None)
        if extensions is super_extensions:
            default_extension = f'.{name.lower()}'
            cls.formats[default_extension] = cls
            cls.extensions = [default_extension]
        else:
            cls.formats.update(
                {
                    f'.{ext}' if not ext.startswith('.') else ext: cls
                    for ext in cls.extensions
                }
            )


@dataclasses.dataclass
class Data(abc.ABC, metaclass=DataMeta):
    _file: filelike | None = None
    format: T.ClassVar[formatlike|None] = ezpyzy.format.Pickle

    serialized_in_binary: T.ClassVar[bool] = True

    def __post_init__(self):
        self._file = Cache(self._file, format=type(self)) if self._file is not None else None

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, file):
        self._file = Cache(file, format=type(self)) if file is not None else None

    @classmethod
    def deserialize(cls, string, *args, **kwargs):
        return cls.format.deserialize(string, *args, **kwargs) # noqa

    def serialize(self, *args, **kwargs):
        return self.format.serialize(self, *args, **kwargs) # noqa

    def save(self, file=None, *args, **kwargs):
        original_file = self._file
        file = Cache(self._file if file is None else file, format=type(self))
        assert file.path is not None
        self._file = str(file.path)
        file.save(self, *args, **kwargs)
        self._file = original_file

    @classmethod
    def load(cls: type[C], file:filelike, *args, **kwargs) -> C:
        file = Cache(file, format=cls)
        obj = file.load(*args, **kwargs)
        obj._file = file
        return obj



if __name__ == '__main__':

    @dataclasses.dataclass
    class Foo(Data):
        x: int = None
        y: float = None

    foo = Foo(x=1, y=2, _file='blah.txt')
    print(foo)
    print(foo.file)