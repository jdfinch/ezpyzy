
from __future__ import annotations

import inspect
import dataclasses as dc
import pathlib as pl
import json
import sys
import copy as cp

from ezpyzy.setter import setters
from ezpyzy.import_path import get_import_path, import_obj_from_path

import typing as T


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


class Configured:
    def __init__(self, object, fields, configured, args):
        self.object: Config = object
        self.and_unconfigured: dict[str, None] = fields
        self.configured: dict[str, None] = configured
        self.initialized: bool = False
        self.args: dict[str, T.Any]|None = args
    def __bool__(self):
        return self.initialized
    def __contains__(self, field: str):
        return field in self.configured
    def __iter__(self):
        return iter(self.configured)
    def __getattr__(self, field: str):
        return field in self.configured
    def __iadd__(self, field: str):
        if isinstance(getattr(self.object, field), Config):
            pass
        else:
            self.configured[field] = None
    def __isub__(self, other):
        self.configured.pop(other, None)
    def __setattr__(self, field, value):
        if field in ('object', 'and_unconfigured', 'configured', 'initialized'):
            super().__setattr__(field, value)
        elif isinstance(getattr(self.object, field), (Config, Configs)):
            pass
        elif value:
            self.configured[field] = None
        else:
            self.configured.pop(field, None)
    @property
    def unconfigured(self):
        return {k: v for k, v in self.and_unconfigured.items() if k not in self.configured}

    def dict(self):
        module = sys.modules[self.object.__class__.__module__]
        encoder = ConfigJSONEncoder(module)
        return encoder.default(self.object)

    def json(self, indent=2):
        module = sys.modules[self.object.__class__.__module__]
        encoder = ConfigJSONEncoder(module, indent=indent)
        return encoder.encode(self.object)

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


class ConfigMeta(type):
    configured: Configured
    def __new__(cls, name, bases, attrs):
        cls = super().__new__(cls, name, bases, attrs)
        cls = dc.dataclass(cls) # noqa
        cls = setters(cls)
        fields = {field.name: None for field in dc.fields(cls)}
        init = getattr(cls, '__init__', lambda self: None)
        init_sig = inspect.signature(init)
        def __init__(self, *args, **kwargs):
            arguments = init_sig.bind(self, *args, **kwargs).arguments
            self.configured = Configured(object=self, fields=fields,
                configured={k: v for k, v in arguments.items()
                if k in fields and v is not inspect.Parameter.empty},
                args=arguments)
            init(self, *args, **kwargs) # noqa
            self.configured.initialized = True
            self.configured.args = None
        cls.__init__ = __init__
        return cls


class Config(metaclass=ConfigMeta):
    base: str | pl.Path | 'Config' | None = None

    def __post_init__(self):
        if not self.configured.base:
            return
        if isinstance(self.base, str) and self.base.lstrip().startswith('{'):
            '''load base from JSON str'''
            decoder = ConfigJSONDecoder(sys.modules[self.__class__.__module__])
            loaded = decoder.decode(self.base)
            base = loaded
            self.base = None
        elif isinstance(self.base, pl.Path) or isinstance(self.base, str):
            '''load base from file'''
            config_path = pl.Path(self.base)
            json_content = config_path.read_text()
            decoder = ConfigJSONDecoder(sys.modules[self.__class__.__module__])
            loaded = decoder.decode(json_content)
            base = loaded
            self.base = str(config_path)
        else:
            '''load base from Config instance, JSON dict, or other object'''
            base = self.base
            self.base = None
        self |= base

    def __setattr__(self, key, value):
        if self.configured:
            self.configured += key
        return super().__setattr__(key, value)

    def __ior__(self, other):
        """
        Update the configuration with the values from another configuration, regardless of whether the fields are configured or not in other.
        """
        if isinstance(other, dict):
            for field in self.configured.and_unconfigured:
                if field in other:
                    if not isinstance(value:=other[field], (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig |= other[field]
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] |= value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        else:
            for field in self.configured.and_unconfigured:
                if hasattr(other, field):
                    if not isinstance(value:=getattr(other, field), (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig |= value
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] |= value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        return self

    def __or__(self, other):
        copy = cp.deepcopy(self)
        copy |= other
        return copy

    def __imul__(self, other):
        """
        Update the configuration with the values from another configuration, only if the fields are configured in other (if other is not a Config object, this does the same as config |= other).
        """
        if isinstance(other, Config):
            for field in self.configured.and_unconfigured:
                if field in other.configured:
                    if not isinstance(value:=getattr(other, field), (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig *= value
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] *= value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        elif isinstance(other, dict):
            for field in self.configured.and_unconfigured:
                if field in other:
                    if not isinstance(value:=other[field], (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig *= value
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] *= value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        else:
            for field in self.configured.and_unconfigured:
                if hasattr(other, field):
                    if not isinstance(value:=getattr(other, field), (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig *= value
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] *= value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        return self

    def __mul__(self, other):
        copy = cp.deepcopy(self)
        copy += other
        return copy

    def __iadd__(self, other):
        """
        Update unconfigured values with another configuration, regardless of whether the fields are configured or not in other.
        """
        if isinstance(other, dict):
            for field in self.configured.unconfigured:
                if field in other:
                    if not isinstance(value:=other[field], (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig += value
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] += value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        else:
            for field in self.configured.unconfigured:
                if hasattr(other, field):
                    if not isinstance(value:=getattr(other, field), (Config, dict)):
                        setattr(self, field, value)
                    elif isinstance(subconfig:=getattr(self, field), Config):
                        subconfig += value
                    elif isinstance(subconfig, Configs):
                        if isinstance(value, dict):
                            for subconfig_key, value_subconfig in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key] += value_subconfig
                                elif isinstance(value_subconfig, Config):
                                    subconfig[subconfig_key] = value_subconfig
                    else:
                        setattr(self, field, value)
                    self.configured += field
        return self

    def __add__(self, other):
        copy = cp.deepcopy(self)
        copy += other
        return copy


class ImmutableConfig(Config):
    def __setattr__(self, key, value):
        if self.configured:
            raise AttributeError(f'ImmutableConfig {self} is immutable after construction.')
        return super().__setattr__(key, value)


E = T.TypeVar('E', bound=Config)

class Configs(dict[str, E]):
    pass



if __name__ == '__main__':

    @dc.dataclass
    class Foo(Config):
        x: int = 1
        y: int = 2

    foo = Foo()

    print(f'{foo = }')