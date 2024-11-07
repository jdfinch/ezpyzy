
from __future__ import annotations

import dataclasses as dc
import json
from dataclasses import dataclass
import inspect as ins
import functools as ft
import pathlib as pl
import copy as cp
import sys

from ezpyzy.setter import setters
from ezpyzy.import_path import get_import_path, import_obj_from_path

import typing as T


class Arguments:
    def __init__(self, obj, args):
        self.__obj__ = obj
        self.__args__ = args
    def __iter__(self):
        return iter(self.__args__)
    def __getitem__(self, item):
        return self.__args__[item]
    def __delitem__(self, key):
        del self.__args__[key]
    def __len__(self):
        return len(self.__args__)
    def __contains__(self, item):
        return item in self.__args__
    def __getattr__(self, item):
        return getattr(self.__obj__, item)
    def __setattr__(self, key, value):
        if key in ('__obj__', '__args__'):
            object.__setattr__(self, key, value)
        else:
            setattr(self.__obj__, key, value)
            self.__setattr__(key, value)
            self.__obj__.undefined.discard(key)
    def __delattr__(self, item):
        del self.__args__[item]
    def __str__(self):
        return f"Arguments({self.__args__})"
    def __repr__(self):
        return str(self)




def config(cls=None, **kwargs):
    if cls is None:
        return ft.partial(config, **kwargs)
    cls = dc.dataclass(cls)
    cls = setters(cls)
    init = getattr(cls, '__init__', lambda self: None)
    init_sig = ins.signature(init)
    def __init__(self, *args, **kwargs):
        self.__dict__['__mutable__'] = True
        # self.defaults = {
        #     **{p.name: p.default for p in init_sig.parameters.values() if p.default is not p.empty},
        #     **{f.name: f.default for f in dc.and_unconfigured(cls) if f.default is not dc.MISSING},
        #     **{f.name: f.default_factory() for f in dc.and_unconfigured(cls) if f.default_factory is not dc.MISSING},
        # }
        bound = init_sig.bind(self, *args, **kwargs).arguments
        self.args = Arguments(self, {k: v for i, (k, v) in enumerate(bound.items()) if i})
        self.undefined = {f.name for f in dc.fields(cls) if f.name not in self.args}
        init(self, *args, **kwargs) # noqa
        del self.args
        # del self.defaults
        del self.__mutable__
    cls.__init__ = __init__
    return cls


F = T.TypeVar('F', bound=T.Callable)


def take_defaults_from_self(method: F) -> F:
    sig = ins.signature(method)
    @ft.wraps(method)
    def wrapper_method(self, *args, **kwargs):
        binding = sig.bind(self, *args, **kwargs)
        arguments = binding.arguments
        from_self = {k: getattr(self, k) for k in sig.parameters if k not in arguments and hasattr(self, k)}
        arguments.update(from_self)
        result = method(*binding.args, **binding.kwargs)
        return result
    return wrapper_method


class ConfigJSONDecoder(json.JSONDecoder):
    def __init__(self, module, *args, **kwargs):
        self.module = module
        self.configs = {}
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '__class__' in obj:
            cls = import_obj_from_path(obj.pop('__class__'))
            fields = {field.name for field in dc.fields(cls)}
            config = cls(**{var: val for var, val in obj.items() if var in fields})
            self.configs.setdefault(cls, []).append(config)
            return config
        else:
            return obj

class ConfigJSONEncoder(json.JSONEncoder):
    def __init__(self, module, *args, **kwargs):
        self.module = module
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, Config):
            json = {field.name: getattr(obj, field.name) for field in dc.fields(obj)} # noqa
            json['__class__'] = get_import_path(obj.__class__)
            imported_cls = import_obj_from_path(json['__class__'])
            assert imported_cls is obj.__class__
            return json
        else:
            return super().default(obj)


@config
@dc.dataclass
class Config:
    base: str | pl.Path | Config | None = None
    args: T.ClassVar[Arguments[str, T.Any]]
    undefined: T.ClassVar[set[str]]
    __mutable__ = True
    # defaults: T.ClassVar[dict[str, T.Any]]

    def __post_init__(self):
        if 'base' in self.args and (config_arg := self.args.base) is not None:
            del self.args.base
            self.base = None
            serialized = None
            serialized_subpath = None
            if not hasattr(self, 'undefined'):
                self.undefined = set()  # noqa
            if isinstance(config_arg, str):
                if config_arg.lstrip().startswith('{'):
                    serialized = config_arg
                else:
                    config_arg, *serialized_subpath = config_arg.split(' => ')
                    config_arg = pl.Path(config_arg).expanduser()
            if isinstance(config_arg, pl.Path):
                if config_arg.exists():
                    if config_arg.is_dir():
                        config_arg = config_arg / 'config.json'
                        if not config_arg.exists():
                            raise ValueError(f'base is a directory that does not contain a config.json: {config_arg}')
                    serialized = config_arg.read_text()
                    self.base = str(config_arg)
                    self.undefined.discard('base')
                else:
                    raise ValueError(f'base is not a path that exists: {config_arg}')
            if serialized is not None:
                decoder = ConfigJSONDecoder(module=sys.modules[self.__class__.__module__])
                branch = decoder.decode(serialized)
                if serialized_subpath:
                    if serialized_subpath == ('',):
                        loaded_config = branch
                    else:
                        for subpath in serialized_subpath:
                            if isinstance(branch, dict):
                                branch = branch[subpath]
                            elif isinstance(branch, list):
                                branch = branch[int(subpath)]
                            else:
                                branch = getattr(branch, subpath)
                        loaded_config = branch
                else:
                    loaded_config = decoder.configs[self.__class__][-1]
                config_base = vars(loaded_config)
            elif isinstance(config_arg, Config):
                config_base = vars(config_arg)                  # copy Config
            elif isinstance(config_arg, dict):
                config_base = config_arg                        # copy dict as Config
            else:
                config_base = vars(config_arg)                  # copy object as Config
            for var in (field.name for field in dc.fields(self) if field.name in config_base):
                self_val = getattr(self, var)
                base_val = config_base[var]
                if var in self.undefined:
                    if isinstance(self_val, Config):
                        self_val.base = base_val
                        self_val.args = dict(config=base_val) # noqa
                        self_val.__post_init__()
                        del self_val.args
                    else:
                        setattr(self, var, base_val)
                elif isinstance(self_val, Config):
                    self_val.base = base_val
                    self_val.args = dict(config=base_val)  # noqa
                    self_val.__post_init__()
                    del self_val.args
        else:
            self.undefined = {f.name for f in dc.fields(self) if f.name not in self.args}  # noqa

    def dict(self):
        module = self.__class__.__module__
        encoder = ConfigJSONEncoder(module=sys.modules[module])
        serialized = encoder.default(self)
        return serialized

    def json(self, indent=2):
        module = self.__class__.__module__
        encoder = ConfigJSONEncoder(module=sys.modules[module], indent=indent)
        serialized = encoder.encode(self)
        return serialized

    def save(self, path:str|pl.Path=None, indent:int|None=2):
        serialized = self.json(indent=indent)
        if path is not None:
            path = pl.Path(path).expanduser()
        elif self.base:
            path = pl.Path(self.base)
        else:
            raise ValueError('No path provided and no base path found for saving config.')
        path.write_text(serialized)
        return serialized

    def __ior__(self, other):
        assert isinstance(other, Config), f'Cannot merge Config with {type(other)}'
        for field in dc.fields(other):
            if field.name not in other.undefined:
                setattr(self, field.name, getattr(other, field.name))
                self.undefined.discard(field.name)
        return self

    def __or__(self, other):
        assert isinstance(other, Config), f'Cannot merge Config with {type(other)}'
        merged = cp.deepcopy(self)
        merged |= other
        return merged

    def __setattr__(self, key, value):
        if not isinstance(self.__dict__.get('args', None), Arguments) and 'undefined' in self.__dict__:
            self.undefined.discard(key)
        return object.__setattr__(self, key, value)


@config
@dc.dataclass
class ImmutableConfig(Config):
    __mutable__ = False

    def __setattr__(self, key, value):
        if not getattr(self, '__mutable__', True):
            raise AttributeError(f'ImmutableConfig {self} is immutable.')
        super().__setattr__(key, value)



def default(x) -> ...:
    if callable(x) and getattr(x, '__name__', None) == "<lambda>":
        return dc.field(default_factory=x)
    else:
        # if isinstance(x, Config):
        #     x.undefined = {f.name for f in dc.and_unconfigured(x)} # noqa
        return dc.field(default_factory=ft.partial(cp.deepcopy, x))



if __name__ == '__main__':

    vars().update(dataclass=config) # noqa

    @dataclass
    class A(Config):
        x: int = -1
        y: int|float = 1
        z: list[str] = dc.field(default_factory=list)

        def __post_init__(self):
            for base in A.__bases__: base.__post_init__(self) # noqa
            print(f'{self.args = }')

        @take_defaults_from_self
        def foo(self, x=None, z=None):
            print('Foo!', f'{x = }', f'{z = }')
            self.x = x
            self.z = z

        def _set_y(self, value):
            return value * 2


    @dataclass
    class B(A):
        z: list[str] = dc.field(default_factory=lambda: [1, 2, 3])


    @dataclass
    class C(Config):
        a: A = None
        b: B = None

    a = A(x=1, y=2)
    print(f'{a = }')
    print(f'{vars(a) = }')
    b = B(x=8)
    print(f'{b = }')

    b.foo(3)
    b.foo(z=[7, 9])

    c = C(a=a, b=b)

    cereal = c.save()
    print(cereal)
    c2 = C(cereal, b=B(y=92.4))
    print(c2)
    print(c2.save())







