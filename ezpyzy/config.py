
from __future__ import annotations

import inspect
import dataclasses as dc
import pathlib as pl
import json
import sys
import copy as cp
import functools as ft
import re

from ezpyzy.setter import setters
from ezpyzy.import_path import get_import_path, import_obj_from_path

import typing as T

ClassVar_pattern = re.compile(r'\bClassVar\b')

def default(x) -> ...:
    if callable(x) and getattr(x, '__name__', None) == "<lambda>":
        return dc.field(default_factory=x)
    else:
        return dc.field(default_factory=ft.partial(cp.deepcopy, x))


class ConfigFields(dict[str, None]):
    def __init__(self, object, which_fields_serialization_strategy):
        dict.__init__(self)
        self.object = object
        self._which_fields_serialization_strategy = which_fields_serialization_strategy

    def dict(self):
        encoder = ConfigJSONEncoder(which=self._which_fields_serialization_strategy)
        return encoder.default(self.object)

    def json(self, indent=2):
        encoder = ConfigJSONEncoder(which=self._which_fields_serialization_strategy, indent=indent)
        return encoder.encode(self.object)

    def save(self, path: str | pl.Path = None, indent: int | None = 2):
        serialized = self.json(indent=indent)
        if path is not None:
            path = pl.Path(path).expanduser()
        elif self.object.base:
            path = pl.Path(self.object.base)
        else:
            raise ValueError('No path provided and no base path found for saving config.')
        path.write_text(serialized)
        return serialized


class Configured:
    def __init__(self, object, fields, args):
        self.object: Config = object
        self.and_unconfigured_and_subconfigs: ConfigFields[str, None] = ConfigFields(object, 'all')
        self.and_unconfigured_and_subconfigs.update(fields)
        self.subconfigs: ConfigFields[str, None] = ConfigFields(object, 'subconfigs')
        self.and_unconfigured: ConfigFields[str, None] = ConfigFields(object, 'and_unconfigured')
        self.and_unconfigured.update(fields)
        self.configured: ConfigFields[str, None] = ConfigFields(object, 'configured')
        self.initialized: bool = False
        self.args: dict[str, T.Any]|None = args

    def __bool__(self):
        return self.initialized

    def __contains__(self, field: str):
        return field in self.configured

    def __iter__(self):
        return iter(self.configured)

    def __iadd__(self, field: str):
        if field not in self.and_unconfigured_and_subconfigs:
            pass
        elif isinstance(getattr(self.object, field, None), (Config, MultiConfig)):
            self.subconfigs[field] = None
            self.configured.pop(field, None)
            self.and_unconfigured.pop(field, None)
        else:
            self.configured[field] = None
            self.subconfigs.pop(field, None)
        return self

    def __isub__(self, field):
        if field not in self.and_unconfigured_and_subconfigs:
            pass
        elif isinstance(getattr(self.object, field, None), (Config, MultiConfig)):
            self.subconfigs[field] = None
            self.and_unconfigured.pop(field, None)
        else:
            self.subconfigs.pop(field, None)
        self.configured.pop(field, None)
        return self

    def __setattr__(self, field, value):
        if field in (
            'object', 'and_unconfigured_and_subconfigs', 'subconfigs', 'and_unconfigured', 'configured',
            'initialized', 'args'
        ):
            super().__setattr__(field, value)
        elif field not in self.and_unconfigured_and_subconfigs:
            pass
        elif value:
            self.__iadd__(field)
        else:
            self.__isub__(field)

    @property
    def and_subconfigs(self) -> ConfigFields[str, None]:
        config_fields = ConfigFields(self.object, 'and_subconfigs')
        config_fields.update({k: v for k, v in self.and_unconfigured_and_subconfigs.items()
            if k in self.subconfigs or k in self.configured})
        return config_fields

    @property
    def unconfigured(self) -> ConfigFields[str, None]:
        config_fields = ConfigFields(self.object, 'unconfigured')
        config_fields.update({k: v for k, v in self.and_unconfigured.items() if k not in self.configured})
        return config_fields

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
        elif self.object.base:
            path = pl.Path(self.object.base)
        else:
            raise ValueError('No path provided and no base path found for saving config.')
        path.write_text(serialized)
        return serialized

    def __str__(self):
        return f"{self.object.__class__.__name__}(configured={{{', '.join(self.configured)}}}, subconfigs={{{', '.join(self.subconfigs)}}})"


class ConfigMeta(type):
    configured: Configured

    def __new__(cls, name, bases, attrs):
        for attr, default_value in attrs.items():
            if (attr in attrs.get('__annotations__', {})
                and ClassVar_pattern.search(str(attrs['__annotations__'][attr])) is None
                and not isinstance(default_value, (str, int, float, bool, frozenset))
            ):
                attrs[attr] = default(default_value)
        cls = super().__new__(cls, name, bases, attrs)
        cls = dc.dataclass(cls) # noqa
        cls = setters(cls)
        fields = {field.name: None for i, field in enumerate(dc.fields(cls)) if i > 0}
        init = getattr(cls, '__init__', lambda self: None)
        init_sig = inspect.signature(init)
        def __init__(self, *args, **kwargs):
            arguments = init_sig.bind(self, *args, **kwargs).arguments
            self.configured = Configured(object=self, fields=fields, args=arguments)
            for argument in arguments:
                self.configured += argument
            init(self, *args, **kwargs) # noqa
            self.configured.initialized = True
            self.configured.args = None
        for attr, value in attrs.items():
            setattr(cls, attr, value)
        cls.__init__ = __init__
        return cls


@dc.dataclass
class Config(metaclass=ConfigMeta):
    configured: T.ClassVar[Configured]
    base: str | pl.Path | 'Config' | None = None

    def __post_init__(self):
        if not self.base:
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
        self **= base

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if hasattr(self, 'configured'):
            if self.configured:
                self.configured.__iadd__(key)
            elif isinstance(value, (Config, MultiConfig)):
                self.configured.__isub__(key)
        return

    def __ior__(self, other):
        """
        Update the configuration with the values from another configuration, regardless of whether the and_unconfigured_and_subconfigs are configured or not in other.
        """
        if isinstance(other, dict):
            contains = lambda o, f: f in o
            get = lambda o, f: o[f]
        else:
            contains = lambda o, f: hasattr(o, f)
            get = lambda o, f: getattr(o, f)
        for field in self.configured.and_unconfigured:
            if contains(other, field):
                setattr(self, field, get(other, field))
        for field in self.configured.subconfigs:
            if contains(other, field):
                subconfig = getattr(self, field)
                value = get(other, field)
                if isinstance(subconfig, Config):
                    if isinstance(value, (Config, dict)) and not isinstance(value, MultiConfig):
                        subconfig.__ior__(value)
                    else:
                        setattr(self, field, value)
                elif isinstance(subconfig, MultiConfig):
                    if isinstance(value, dict) and not isinstance(value, Config):
                        for subconfig_key, value in value.items():
                            if subconfig_key in subconfig:
                                subconfig[subconfig_key].__ior__(value)
                            elif isinstance(value, Config):
                                subconfig[subconfig_key] = value
                    else:
                        setattr(self, field, value)
                else:
                    setattr(self, field, value)
        return self

    def __or__(self, other):
        copy = cp.deepcopy(self)
        copy.__ior__(other)
        return copy

    def __iand__(self, other):
        """
        Update the configuration with the values from another configuration, only if fields are configured in other.
        """
        if isinstance(other, Config):
            for field in self.configured.and_unconfigured:
                if field in other.configured:
                    setattr(self, field, getattr(other, field))
            for field in self.configured.subconfigs:
                if hasattr(other, field):
                    subconfig = getattr(self, field)
                    value = getattr(other, field)
                    if isinstance(subconfig, Config):
                        if isinstance(value, (Config, dict)) and not isinstance(value, MultiConfig):
                            subconfig.__iand__(value)
                        else:
                            setattr(self, field, value)
                    elif isinstance(subconfig, MultiConfig):
                        if isinstance(value, dict) and not isinstance(value, Config):
                            for subconfig_key, value in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key].__iand__(value)
                        else:
                            setattr(self, field, value)
        elif isinstance(other, dict):
            for field in self.configured.and_unconfigured:
                if field in other:
                    setattr(self, field, other[field])
            for field in self.configured.subconfigs:
                if field in other:
                    subconfig = getattr(self, field)
                    value = other[field]
                    if isinstance(subconfig, Config):
                        if isinstance(value, (Config, dict)) and not isinstance(value, MultiConfig):
                            subconfig.__iand__(value)
                        else:
                            setattr(self, field, value)
                    elif isinstance(subconfig, MultiConfig):
                        if isinstance(value, dict) and not isinstance(value, Config):
                            for subconfig_key, value in value.items():
                                if subconfig_key in subconfig:
                                    subconfig[subconfig_key].__iand__(value)
                        else:
                            setattr(self, field, value)
        return self

    def __and__(self, other):
        copy = cp.deepcopy(self)
        copy.__iand__(other)
        return copy

    def __imul__(self, other):
        """
        Update only UNconfigured fields with values from another configuration (it does not matter whether the fields are configured in other).
        """
        if isinstance(other, dict):
            contains = lambda o, f: f in o
            get = lambda o, f: o[f]
        else:
            contains = lambda o, f: hasattr(o, f)
            get = lambda o, f: getattr(o, f)
        for field in self.configured.unconfigured:
            if contains(other, field):
                setattr(self, field, get(other, field))
        for field in self.configured.subconfigs:
            if contains(other, field):
                subconfig = getattr(self, field)
                value = get(other, field)
                if isinstance(subconfig, Config):
                    if isinstance(value, (Config, dict)) and not isinstance(value, MultiConfig):
                        subconfig.__imul__(value)
                elif isinstance(subconfig, MultiConfig) and isinstance(value, dict) and not isinstance(value, Config):
                    for subconfig_key, value in value.items():
                        if subconfig_key in subconfig:
                            subconfig[subconfig_key].__imul__(value)
        return self

    def __mul__(self, other):
        copy = cp.deepcopy(self)
        copy.__imul__(other)
        return copy

    def __ipow__(self, other):
        """
        Update only UNconfigured fields with values from another configuration (it does not matter whether the fields are configured in other). Configs in MultiConfig fields that exist in other but not in self are added to self.
        """
        if isinstance(other, dict):
            contains = lambda o, f: f in o
            get = lambda o, f: o[f]
        else:
            contains = lambda o, f: hasattr(o, f)
            get = lambda o, f: getattr(o, f)
        for field in self.configured.unconfigured:
            if contains(other, field):
                setattr(self, field, get(other, field))
        for field in self.configured.subconfigs:
            if contains(other, field):
                subconfig = getattr(self, field)
                value = get(other, field)
                if isinstance(subconfig, Config):
                    if isinstance(value, (Config, dict)) and not isinstance(value, MultiConfig):
                        subconfig.__imul__(value)
                elif isinstance(subconfig, MultiConfig) and isinstance(value, dict) and not isinstance(value, Config):
                    for subconfig_key, value in value.items():
                        if subconfig_key in subconfig:
                            subconfig[subconfig_key].__imul__(value)
                        elif isinstance(value, Config):
                            subconfig[subconfig_key] = value
        return self

    def __pow__(self, other):
        copy = cp.deepcopy(self)
        copy.__ipow__(other)
        return copy


class ImmutableConfig(Config):
    def __setattr__(self, key, value):
        if self.configured:
            raise AttributeError(f'ImmutableConfig {self} is immutable after construction.')
        return super().__setattr__(key, value)


CONFIG = T.TypeVar('CONFIG')

class MultiConfig(dict[str, CONFIG]):
    def __init__(self,
        configs_:T.Iterable[tuple[str, CONFIG]]|T.Mapping[str, CONFIG]=(),
        /, **configs: CONFIG):
        dict.__init__(self)
        self.update(configs_)
        self.update(configs)

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
    def __init__(self, module = None,
        which: T.LiteralString = "all",
        *args, **kwargs):
        self.module = module
        self.which_fields = which
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, Config):
            which = dict(all='and_unconfigured_and_subconfigs').get(self.which_fields, self.which_fields)
            fields_to_serialize = getattr(obj.configured, which)
            json = {field: getattr(obj, field) for field in fields_to_serialize}
            if self.module is not None and self.which_fields == 'all':
                json['__class__'] = get_import_path(obj.__class__)
                imported_cls = import_obj_from_path(json['__class__'])
                assert imported_cls is obj.__class__
            return json
        else:
            return super().default(obj)


if __name__ == '__main__':

    @dc.dataclass
    class Foo(Config):
        x: int = 1
        y: int = 2

    foo = Foo()

    print(f'{foo = }')