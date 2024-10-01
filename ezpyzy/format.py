
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

class PyLS2(Savable):
    extension = ['pyls2']

    @classmethod
    def deserialize(cls, string):
        tree = ast.parse(string, mode='eval')
        transformed = _empty_set_transformer.visit(tree)
        return ast.literal_eval(transformed)

    def serialize(self: ..., *args, **kwargs):
        serialized = repr(self)
        PyLS2.deserialize(serialized)
        return serialized


_forbidden_raw_chars = set('\n\t')

class PyLS(Savable):
    """"
    Python Literal Serialization (PyLS) is a format for serializing Python literals as strings.
    """
    extension = ['pyls']

    @classmethod
    def deserialize(cls, string):
        try:
            tree = ast.parse(string, mode='eval')
            transformed = _empty_set_transformer.visit(tree)
            return ast.literal_eval(transformed)
        except Exception:
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


class TSPy(Savable):
    """
    Table of Python Literal Serializations (TSPy), ultimately a TSV file.
    """

    extensions = ['tspy', 'tabpyls', 'tspyls', 'tspl', 'tspyl', 'tsl', 'tsp']

    @classmethod
    def deserialize(cls, string):
        return [[PyLS.deserialize(cell) for cell in row.split('\t')] for row in string.split('\n') if row]

    def serialize(self: ..., *args, **kwargs):
        return '\n'.join('\t'.join(PyLS.serialize(cell) for cell in row) for row in self)



if __name__ == '__main__':

    from ezpyzy.timer import Timer

    def get_cells(s):
        cells = [[cell for cell in row.split('\t')] for row in s.split('\n')]
        return cells

    def scan_cells(table):
        for i, row in enumerate(table):
            for j, cell in enumerate(row):
                if not cell or cell[0] not in '\'"[({0123456789-' and cell not in {'True', 'False', 'None'}:
                    table[i][j] = repr(cell)

    def big_literal_parse(table):
        big_literal = ''.join(('[', ','.join((''.join(('[', ','.join(row), ']'))) for row in table), ']'))
        big_parse = ast.literal_eval(big_literal)
        return big_parse


    def pon_parse(s):
        rows = [[]]
        stack = [['', []]]
        lastchar = ''
        for ch in s:
            context, item = stack[-1]
            if context == '':  # root context
                if ch == '"':
                    stack.append(['"str', []])
                elif ch == "'":
                    stack.append(["'str", []])
                elif ch == '[':
                    stack.append(['list', []])
                elif ch == '{':
                    stack.append(['dict|set', []])
                elif ch == '(':
                    stack.append(['tuple', []])
                elif ch in '0123456789-':
                    stack.append(['number', [ch]])
                elif ch == '\t':
                    if stack[-1][1]:
                        rows[-1].append(stack[-1][1][-1])
                        stack[-1][1] = []
                    else:
                        rows[-1].append(None)
                elif ch == '\n':
                    if stack[-1][1]:
                        rows[-1].append(stack[-1][1][-1])
                        stack[-1][1] = []
                    rows.append([])
                else:
                    stack.append(['text', [ch]])
            elif context == 'text':
                if ch == '\t':
                    stack.pop()
                    item = ''.join(item)
                    if item[:5] in {'True', 'False', 'None', 'set()'}:
                        if item == 'set()':
                            item = set()
                        else:
                            item = {'True': True, 'False': False, 'None': None}.get(item, item)
                    rows[-1].append(item)
                elif ch == '\n':
                    stack.pop()
                    item = ''.join(item)
                    if item[:5] in {'True', 'False', 'None', 'set()'}:
                        if item == 'set()':
                            item = set()
                        else:
                            item = {'True': True, 'False': False, 'None': None}.get(item, item)
                    rows[-1].append(item)
                    rows.append([])
                elif len(stack) > 2 and ch in 'e)':
                    item.append(ch)
                    stack.pop()
                    item = ''.join(item)
                    if item[:5] in {'True', 'False', 'None', 'set()'}:
                        if item == 'set()':
                            item = set()
                        else:
                            item = {'True': True, 'False': False, 'None': None}[item]
                    stack[-1][1].append(item)
                else:
                    item.append(ch)
            elif context == '"str':
                if ch == '"' and lastchar != '\\':
                    stack.pop()
                    item = ''.join(item)
                    stack[-1][1].append(item)
                elif lastchar == '\\':
                    if ch == 'n':
                        item.append('\n')
                    elif ch == 't':
                        item.append('\t')
                    elif ch == 'r':
                        item.append('\r')
                    elif ch == 'b':
                        item.append('\b')
                    elif ch == 'f':
                        item.append('\f')
                    elif ch == '\\':
                        item.append('\\')
                    else:
                        raise ValueError(f'Invalid escape sequence: {ch}')
                elif ch == '\\':
                    pass
                else:
                    item.append(ch)
            elif context == "'str":
                if ch == "'" and lastchar != '\\':
                    stack.pop()
                    item = ''.join(item)
                    stack[-1][1].append(item)
                elif lastchar == '\\':
                    if ch == 'n':
                        item.append('\n')
                    elif ch == 't':
                        item.append('\t')
                    elif ch == 'r':
                        item.append('\r')
                    elif ch == 'b':
                        item.append('\b')
                    elif ch == 'f':
                        item.append('\f')
                    elif ch == '\\':
                        item.append('\\')
                    else:
                        raise ValueError(f'Invalid escape sequence: {ch}')
                elif ch == '\\':
                    pass
                else:
                    item.append(ch)
            elif context == 'number':
                if ch in '0123456789-.eE_':
                    item.append(ch)
                elif ch == ',':
                    stack.pop()
                    item = ''.join(item)
                    item = float(item) if '.' in item else int(item)
                    stack[-1][1].append(item)
                elif ch == '\t':
                    stack.pop()
                    item = ''.join(item)
                    item = float(item) if '.' in item else int(item)
                    rows[-1].append(item)
                elif ch == '\n':
                    stack.pop()
                    item = ''.join(item)
                    item = float(item) if '.' in item else int(item)
                    rows[-1].append(item)
                    rows.append([])
            elif context == 'list':
                if ch == ']':
                    stack.pop()
                    stack[-1][1].append(item)
                elif ch == ',':
                    pass
                elif ch == '"':
                    stack.append(['"str', []])
                elif ch == "'":
                    stack.append(["'str", []])
                elif ch == '[':
                    stack.append(['list', []])
                elif ch == '{':
                    stack.append(['dict|set', []])
                elif ch == '(':
                    stack.append(['tuple', []])
                elif ch in '0123456789-':
                    stack.append(['number', [ch]])
                else:
                    stack.append(['text', [ch]])
            elif context == 'tuple':
                if ch == ')':
                    stack.pop()
                    stack[-1][1].append(tuple(item))
                elif ch == ',':
                    pass
                elif ch == '"':
                    stack.append(['"str', []])
                elif ch == "'":
                    stack.append(["'str", []])
                elif ch == '[':
                    stack.append(['list', []])
                elif ch == '{':
                    stack.append(['dict|set', []])
                elif ch == '(':
                    stack.append(['tuple', []])
                elif ch in '0123456789-':
                    stack.append(['number', [ch]])
                else:
                    stack.append(['text', [ch]])
            elif context == 'dict|set':
                if ch == '}':
                    stack.pop()
                    stack[-1][1].append(set(item) if item else {})
                elif ch == ',':
                    pass
                elif ch == ':':
                    stack[-1][0] = 'dict'
                elif ch == '"':
                    stack.append(['"str', []])
                elif ch == "'":
                    stack.append(["'str", []])
                elif ch == '[':
                    stack.append(['list', []])
                elif ch == '{':
                    stack.append(['dict|set', []])
                elif ch == '(':
                    stack.append(['tuple', []])
                elif ch in '0123456789-':
                    stack.append(['number', [ch]])
                else:
                    stack.append(['text', [ch]])
            elif context == 'dict':
                if ch == '}':
                    stack.pop()
                    stack[-1][1].append(dict(zip(item[::2], item[1::2])))
                elif ch == ',':
                    pass
                elif ch == '"':
                    stack.append(['"str', []])
                elif ch == "'":
                    stack.append(["'str", []])
                elif ch == '[':
                    stack.append(['list', []])
                elif ch == '{':
                    stack.append(['dict|set', []])
                elif ch == '(':
                    stack.append(['tuple', []])
                elif ch in '0123456789-':
                    stack.append(['number', [ch]])
                else:
                    stack.append(['text', [ch]])
            elif context == 'set':
                if ch == '}':
                    stack.pop()
                    stack[-1][1].append(set(item))
                elif ch == ',':
                    pass
                elif ch == '"':
                    stack.append(['"str', []])
                elif ch == "'":
                    stack.append(["'str", []])
                elif ch == '[':
                    stack.append(['list', []])
                elif ch == '{':
                    stack.append(['dict|set', []])
                elif ch == '(':
                    stack.append(['tuple', []])
                elif ch in '0123456789-':
                    stack.append(['number', [ch]])
                else:
                    stack.append(['text', [ch]])
            lastchar = ch
        return rows



    def main():

        table = [
            ['Column A', 'colB', 'C.o.l, C', 'Col\tD'],
            ['abc', None, 5, 'This is a test.'],
            ['X\tY', 'W\nZ', 'True', True],
            ['!!!', -9.21, 8e12, [1, 2, 3]],
            [set(), ('a', 'b',), {}, {1: {'a', 'b'}, 2: (), 3: [1, 2]}]
        ] * int(1)

        serialized = TSPy.serialize(table)
        # print(f'{type(serialized).__name__} {serialized = }')

        with Timer('Fast custom parser...'):
            rows = pon_parse(serialized)

        print('hello')

        with Timer('Deserializing PyLS...'):
            deserialized = TSPy.deserialize(serialized)
        # print('\n\n')
        # print(f'{type(deserialized).__name__} {deserialized = }')
        # print('\n\n')
        # print(f'{type(deserialized[4][3][1]).__name__ = }')

        # with Timer('Fast Deserialize PyLS...'):
        #     with Timer('Parsing cells...'):
        #         cells = get_cells(serialized)
        #     with Timer('Scanning cells...'):
        #         scan_cells(cells)
        #     with Timer('Big literal parse...'):
        #         deserialized = big_literal_parse(cells)



        json_table = [
            ['"Column A"', '"colB"', '"C.o.l, C"', '"Col\tD"'],
            ['"abc"', 'null', '5', '"This is a test."'],
            ['"X\tY"', '"W\nZ"', '"True"', 'true'],
            ['"!!!"', '-9.21', '8e12', '[1, 2, 3]'],
            ['[]', '("a", "b",)', '{}', '{"1": ["a", "b"], "2": (), "3": [1, 2]}']
        ] * int(10e4)

        serialized = '\n'.join('\t'.join(json.dumps(cell) for cell in row) for row in json_table)

        with Timer('Deserializing JSON...'):
            deserialized = TSPy.deserialize(serialized)


    main()
