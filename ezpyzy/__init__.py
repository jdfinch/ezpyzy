
from __future__ import annotations

import termios

from ezpyzy.alphanumeral import alphanumeral, alphanumerals
import ezpyzy.ansi as ansi
from ezpyzy.batch import batching, batched
from ezpyzy.bind import bind
from ezpyzy.cache import cache
from ezpyzy.cat import cat
from ezpyzy.config import config, defaults_from_self, Config
from ezpyzy.test import test, Tests, Test, tests, test_groups
from contextlib import nullcontext as collapsable # noqa
from ezpyzy.debugging import debugging
from ezpyzy.default import default
from ezpyzy.denominate import denominate
from ezpyzy.expydite import explore
from ezpyzy.file import File, filelike
from ezpyzy.format import Savable, Text, CSV, JSON, Bytes, Pickle, TSV, Pyr, formatlike
from ezpyzy.get_import_path import get_import_path
from ezpyzy.multiprocess import multiprocess
from ezpyzy.peek import peek
from dataclasses import replace as copy # noqa
from ezpyzy.scope import Scope
from ezpyzy.send_email import send_email as email
from ezpyzy.short_uuid import short_uuid as uuid
from ezpyzy.shush import shush
from ezpyzy.singleton import Singleton, SingletonMeta
from ezpyzy.subproc import subproc
from ezpyzy.timer import Timer
from ezpyzy.table import Table, Row, Column, Col

try:
    from ezpyzy.terminal_environment import TerminalEnvironment
except termios.error:
    pass

try:
    from ezpyzy.fixture_group import fixture_group
except ImportError:
    pass