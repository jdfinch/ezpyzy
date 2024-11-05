
from __future__ import annotations

import json
import pathlib as pl
import sys
import importlib as imp
import itertools as it
from ezpyzy.alphanumeral import alphanumeral
from ezpyzy.import_path import get_import_path, import_obj_from_path


prefix = '~@&MW|'
suffix = '|WM&@~'


class PyrEncoder:
    def __init__(self,): # todo: add compatibility layer to allow unsupported types
        super().__init__()
        self.types = {}
        self.ids = {}
        self.id_generator = iter(alphanumeral(i) for i in it.count())

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


class PyrDecoder:
    def __init__(self): # todo: add compatibility layer to allow unsupported types
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
            t = self.types.setdefault(t, import_obj_from_path(t[1:]))
        if isinstance(t, type):
            o = object.__new__(t) # noqa
        else:
            o = t
        self.swizz[i] = o
        o.__dict__.update((k, (v if isinstance(v, (int, float, bool, type(None))) else (  # noqa
            self.swizz.get(v, v) if isinstance(v, str) else self._decode_obj(v)
        ))) for k, v in data)
        return o


