"""
For use in pytest to easily parameterize tests using fixtures.
"""

import pytest
import sys
import inspect


class fixture_group(list):
    """
    Group fixtures together so that they can be used as a single fixture, like: with fixture_group() as <NAME>: <fixture function definitions>
    """

    def __init__(self):
        list.__init__(self)
        self._enter_vars = {}
        self.name = None

        def meta_fixture(request, **kwargs):
            return kwargs[request.param]

        self.fixture = meta_fixture

    def __enter__(self):
        self._enter_vars = dict(inspect.currentframe().f_back.f_globals)
        return self.fixture

    def __exit__(self, exc_type, exc_val, exc_tb):
        exit_vars = dict(inspect.currentframe().f_back.f_globals)
        for var_name, var_val in exit_vars.items():
            if (
                fixture_group._fixture_marker(var_val) and
                var_val is not self._enter_vars.get(var_name)
            ):
                self.append(var_val)
            elif var_val is self.fixture:
                self.name = var_name
        assert self.name, """fixture_group must be named like:

with fixture_group() as <NAME>:
    ...
"""
        self._enter_vars = {}
        self.fixture.__name__ = self.name
        param = lambda name: inspect.Parameter(
            name, inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        self.fixture.__signature__ = inspect.Signature(
            [param('request')] + [param(name) for name in self.names]
        )
        fx = pytest.fixture(params=self.names)(self.fixture)
        module = sys.modules[exit_vars['__name__']]
        setattr(module, self.name, fx)
        self.fixture = fx

    @property
    def names(self):
        return tuple((fixture_group._fixture_marker(f).name or f.__name__ for f in self))

    @staticmethod
    def _fixture_marker(obj):
        return getattr(obj, '_pytestfixturefunction', False)

