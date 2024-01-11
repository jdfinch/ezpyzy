import functools
import inspect
import typing as T


F = T.TypeVar('F')

def allargs(fn:F=None, **vars_in_or_excluded) -> F:
    if fn is None:
        return functools.partial(allargs, **vars_in_or_excluded)
    if any(vars_in_or_excluded.values() is False):
        inclusive_by_default = True
    else:
        inclusive_by_default = False
    signature = inspect.signature(fn)
    defaults = {
        name: param.default for name, param in signature.parameters.items()
        if param.default is not param.empty
    }
    included = {
        name for name, param in signature.parameters.items()
        if inclusive_by_default and vars_in_or_excluded.get(name, True) or
        not inclusive_by_default and vars_in_or_excluded.get(name, False)
    }
    def wrapper(*args, **kwargs):
        binding = signature.bind(*args, **kwargs)
        specified = {
            name: arg for name, arg in binding.arguments.items()
            if name in included
        }
        result = fn(*args, allargs=specified, **kwargs)
        return result
    return wrapper

