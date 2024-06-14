
from __future__ import annotations


from ezpyzy.batch import batching, batched
from ezpyzy.bind import bind
from ezpyzy.cat import cat
from ezpyzy.check import check
from contextlib import nullcontext as collapsable # noqa
from debugging import debugging
from ezpyzy.default import default
from ezpyzy.denominate import denominate
from ezpyzy.digiterate import digiterate
from ezpyzy.expydite import explore
from ezpyzy.file import File, filelike
from ezpyzy.format import Savable, Text, CSV, JSON, Bytes, Pickle, TSV, PYON, formatlike
from ezpyzy.multiprocess import multiprocess
from ezpyzy.option import option
from ezpyzy.settings import settings, update_settings, replace, undefault, Settings # noqa
from dataclasses import replace as copy # noqa
from ezpyzy.scope import Scope
from ezpyzy.send_email import send_email as email
from ezpyzy.short_uuid import short_uuid as uuid
from ezpyzy.shush import shush
from ezpyzy.singleton import Singleton, SingletonMeta
from ezpyzy.subproc import subproc
from ezpyzy.timer import Timer


try:
    from ezpyzy.fixture_group import fixture_group
except ImportError:
    pass