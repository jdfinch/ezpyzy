from __future__ import annotations

import dataclasses
import typing as T

from ezpyzy.allargs import allargs
from ezpyzy.argcast import argcast
from ezpyzy.autocache import autocache
from ezpyzy.batch import batch, batched
from ezpyzy.bind import bind
from ezpyzy.captured_vars import CapturedVars
from ezpyzy.check import check
from contextlib import nullcontext as collapsable
from ezpyzy.denominate import denominate
from ezpyzy.digital_iteration import digital_iteration
from ezpyzy.expydite import explore
from ezpyzy.file import File, filelike
from ezpyzy.format import Savable, Text, CSV, JSON, Bytes, Pickle, formatlike
from ezpyzy.option import option
# from ezpyzy.protocol import protocol
from ezpyzy.settings import settings, update_settings, replace, undefault, Settings
from dataclasses import replace as copy
from ezpyzy.send_email import send_email as email
from ezpyzy.short_uuid import short_uuid as uuid
from ezpyzy.shush import shush
from ezpyzy.singleton import Singleton, SingletonMeta
from ezpyzy.subproc import subproc
from ezpyzy.table import Table, Column, IDColumn
ColStr = T.Union[Column[str], str, None]
ColInt = T.Union[Column[int], int, None]
ColBool = T.Union[Column[bool], bool, None]
ColFloat = T.Union[Column[float], float, None]
ColObj = T.Union[Column[T.Any], T.Any, None]
ColID = T.Union[IDColumn[str], str, None]
Def: None = lambda x: dataclasses.field(  # noqa
    default_factory=x
    if callable(x) and getattr(x, '__name__', None) == "<lambda>"
    else lambda: x
)
from ezpyzy.timer import Timer

try:
    from ezpyzy.fixture_group import fixture_group
except ImportError:
    pass