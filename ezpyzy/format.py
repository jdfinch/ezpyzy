
from __future__ import annotations

import abc
import ast
import io
import json
import csv
import pickle
import ezpyzy.file
import ezpyzy.pyr as pyon
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

    extensions = ['csv',]

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


class Pyr(Savable):

    extension = ['pyr']

    @classmethod
    def deserialize(cls, string):
        obj = pyon.PyrDecoder().decode(string)
        assert isinstance(obj, cls), f"Pyr object is not of the expected type: {cls}"
        return obj

    def serialize(self: ..., *args, **kwargs):
        return pyon.PyrEncoder().encode(self)


class _EmptySetTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'set' and not node.args:
            return ast.Set(elts=[], ctx=ast.Load())
        else:
            return node
_empty_set_transformer = _EmptySetTransformer()

class PYON(Savable):
    extension = ['pyon']

    @classmethod
    def deserialize(cls, string):
        tree = ast.parse(string, mode='eval')
        transformed = _empty_set_transformer.visit(tree)
        return ast.literal_eval(transformed)

    def serialize(self: ..., *args, **kwargs):
        serialized = repr(self)
        PYON.deserialize(serialized)
        return serialized


_forbidden_raw_chars = set('\n\t')

class PON(Savable):
    extension = ['pon']

    @classmethod
    def deserialize(cls, string):
        try:
            tree = ast.parse(string, mode='eval')
            transformed = _empty_set_transformer.visit(tree)
            return ast.literal_eval(transformed)
        except SyntaxError:
            return string

    def serialize(self: ..., *args, **kwargs):
        if isinstance(self, str) and not set(self) & _forbidden_raw_chars:
            try:
                ast.parse(self, mode='eval')
                transformed = _empty_set_transformer.visit(ast.parse(self, mode='eval'))
                ast.literal_eval(transformed)
            except (SyntaxError, ValueError):
                return self
        return repr(self)


class TSV(Savable):

    extensions = ['tsv',]

    @classmethod
    def deserialize(cls, string):
        return [[PON.deserialize(cell) for cell in row.split('\t')] for row in string.split('\n') if row]

    def serialize(self: ..., *args, **kwargs):
        return '\n'.join('\t'.join(PON.serialize(cell) for cell in row) for row in self)



if __name__ == '__main__':

    def main():

        x = [1, 2, set(), {3: 'hello world'}, {4, 5, None}]

        serialized = PYON.serialize(x)
        print(f'{type(serialized).__name__} {serialized = }')
        deserialized = PYON.deserialize(serialized)
        print('\n\n')
        print(f'{type(deserialized).__name__} {deserialized = }')

    main()
