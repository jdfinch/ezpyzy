
from __future__ import annotations

import abc
import io
import json
import csv
import pickle
import ezpyzy.file
import typing as T


formatlike = T.Union[str, 'Format', T.Type['Format'], None]

formats: dict[str, type['Format']] = {}


class Format(abc.ABC):

    @property
    @abc.abstractmethod
    def is_binary(self): pass

    @abc.abstractmethod
    def serialize(obj: ...) -> str | bytes: pass

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, string: str | bytes) -> T.Any: pass


class SavableMeta(abc.ABCMeta):

    extensions = None

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        extensions = getattr(cls, 'extensions', None)
        super_extensions = getattr(super(cls, cls), 'extensions', None)
        if extensions is super_extensions:
            formats[f'.{name.lower()}'] = cls
        else:
            formats.update({
                f'.{ext}' if not ext.startswith('.') else ext: cls
                for ext in cls.extensions
            })



class Savable(Format, abc.ABC, metaclass=SavableMeta):

    is_binary = False

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, string): pass

    @abc.abstractmethod
    def serialize(self: ...): pass

    def save(self: ..., path):
        file = ezpyzy.file.File(path, format=type(self))
        file.save(self)

    @classmethod
    def load(cls, file):
        file = file.File(file, format=cls)
        obj = file.load()
        return obj


class Text(Savable):

    extensions = ['txt', 'text', 'log', 'out', 'err']

    @classmethod
    def deserialize(cls, string):
        return string

    def serialize(self: ...):
        return str(self)


class Bytes(Savable):

    is_binary = True

    extensions = ['bytes', 'bin', 'binary', 'b']

    @classmethod
    def deserialize(cls, string):
        return string

    def serialize(self: ...):
        return bytes(self)


class JSON(Savable):

    extensions = ['json', 'jsonl']

    @classmethod
    def deserialize(cls, string, *args, **kwargs):
        deserialized = json.loads(string, *args, **kwargs)
        if cls is not JSON:
            deserialized = cls(**deserialized) # noqa
        return deserialized

    def serialize(self: ..., *args, **kwargs):
        if isinstance(self, (dict, list, tuple, str, int, float, bool, type(None))):
            obj = self
        else:
            obj = vars(self)
        return json.dumps(obj, *args, **kwargs)

class CSV(Savable):

    extensions = ['csv', 'tsv']

    @classmethod
    def deserialize(cls, string, *args, **kwargs):
        stream = io.StringIO(string)
        reader = csv.reader(stream, *args, **kwargs)
        return list(reader)

    def serialize(self: ..., *args, **kwargs):
        stream = io.StringIO()
        writer = csv.writer(stream, *args, **kwargs)
        writer.writerows(self) # noqa
        return stream.getvalue()


class Pickle(Savable):

    extensions = ['pkl', 'pickle', 'pckl']
    is_binary = True

    @classmethod
    def deserialize(cls, string, *args, **kwargs):
        return pickle.loads(string, *args, **kwargs)

    def serialize(self: ..., *args, **kwargs):
        return pickle.dumps(self, *args, **kwargs)

