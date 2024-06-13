
from __future__ import annotations

import base64
import json
import pathlib as pl
import sys
import importlib as imp
from ezpyzy.digiterate import digiterate
import hashlib as hl
import base64 as b64

prefix = '~@&MW|'
suffix = '|WM&@~'


class PYONEncoder:
    def __init__(self):
        super().__init__()
        self.types = {}
        self.ids = {}
        self.id_generator = iter(digiterate())

    def encode(self, o):
        t = type(o)
        if t is str:
            return ''.join(('"', o, '"'))
        if t is bool:
            return 'true' if o else 'false'
        if t is type(None):
            return 'null'
        if t in (int, float):
            return repr(o)
        if t is tuple:
            return ''.join((
                '{"tuple":[', ','.join((self.encode(c) for c in o)), ']}'
            ))
        if t is frozenset:
            return ''.join((
                '{"frozenset":[', ','.join((self.encode(c) for c in sorted(o))), ']}'
            ))
        i = id(o)
        if i in self.ids:
            return self.ids[i]
        swizz_id = ''.join((prefix, next(self.id_generator), suffix))
        self.ids[i] = ''.join(('"', swizz_id, '"'))
        if t is list:
            return ''.join((
                '{"list":"', swizz_id, '","":[', ','.join((self.encode(c) for c in o)), ']}'
            ))
        if t is set:
            return ''.join((
                '{"set":"', swizz_id, '","":[', ','.join((self.encode(c) for c in sorted(o))), ']}'
            ))
        if t is dict:
            return ''.join((
                '{"dict":"', swizz_id, '","":[', ','.join((
                    ''.join(('[', self.encode(k), ',', self.encode(v), ']')) for k, v in o.items()
                )), ']}'
            ))
        if t in self.types:
            impath = self.types[t]
        else:
            self.types[t] = impath = get_import_path(t)
        return ''.join((
            '{"^', impath, '":"', swizz_id, '",',
            ','.join(''.join(('"', k, '":', self.encode(v))) for k, v in o.__dict__.items()),
            '}'
        ))


class PYONDecoder:
    def __init__(self):
        super().__init__()
        self.swizz = {}
        self.types = {}
        self.decoder = json.JSONDecoder()

    def decode(self, s):
        j = self.decoder.decode(s)
        if isinstance(j, (str, int, float, bool, type(None))):
            return j
        else:
            return self._decode_obj(j)

    def _decode_obj(self, o):
        keys = iter(o)
        t = next(keys)
        i = o[t]
        if t == 'list':
            data = o['']
            o = []
            self.swizz[i] = o
            o.extend((x if isinstance(x, (int, float, bool, type(None))) else (
                self.swizz.get(x, x) if isinstance(x, str) else self._decode_obj(x)
            )) for x in data)
            return o
        elif t == 'dict':
            data = o['']
            o = {}
            self.swizz[i] = o
            o.update(((k if isinstance(k, (int, float, bool, type(None))) else (
                self.swizz.get(k, k) if isinstance(k, str) else self._decode_obj(k))),
                (v if isinstance(v, (int, float, bool, type(None))) else (
                self.swizz.get(v, v) if isinstance(v, str) else self._decode_obj(v)
            ))) for k, v in data)
            return o
        elif t == 'tuple':
            data = i
            return tuple((x if isinstance(x, (int, float, bool, type(None))) else (
                self.swizz.get(x, x) if isinstance(x, str) else self._decode_obj(x)
            )) for x in data)
        elif t == 'set':
            data = o['']
            o = set()
            self.swizz[i] = o
            o.update((x if isinstance(x, (int, float, bool, type(None))) else (
                self.swizz.get(x, x) if isinstance(x, str) else self._decode_obj(x)
            )) for x in data)
            return o
        elif t == 'frozenset':
            data = i
            return frozenset((x if isinstance(x, (int, float, bool, type(None))) else (
                self.swizz.get(x, x) if isinstance(x, str) else self._decode_obj(x)
            )) for x in data)
        data = [(k, o[k]) for k in keys]
        if t in self.types:
            t = self.types[t]
        else:
            t = self.types.setdefault(t, import_path(t[1:]))
        if isinstance(t, type):
            o = object.__new__(t) # noqa
        else:
            o = t
        self.swizz[i] = o
        o.__dict__.update((k, (v if isinstance(v, (int, float, bool, type(None))) else (
            self.swizz.get(v, v) if isinstance(v, str) else self._decode_obj(v)
        ))) for k, v in data)
        return o



def get_import_path(cls_or_fn):
    name = cls_or_fn.__name__
    module = sys.modules[cls_or_fn.__module__]
    file = module.__file__
    cwd = pl.Path.cwd()
    path = pl.Path(file).relative_to(cwd)
    import_path = '.'.join((*path.parts[:-1], path.stem, name))
    return import_path

def import_path(import_path):
    module, name = import_path.rsplit('.', 1)
    main_module_path = pl.Path(sys.modules['__main__'].__file__)
    cwd = pl.Path.cwd()
    main_module_path = main_module_path.relative_to(cwd)
    main_module = '.'.join((*main_module_path.parts[:-1], main_module_path.stem))
    if module == main_module:
        module = '__main__'
    if module not in sys.modules:
        sys.modules[module] = imp.import_module(module)
    obj = getattr(sys.modules[module], name)
    return obj
