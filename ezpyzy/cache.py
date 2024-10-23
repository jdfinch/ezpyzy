
from __future__ import annotations

from ezpyzy.hash import hash
from ezpyzy.file import File
from ezpyzy.import_path import get_import_path

import inspect as ins

import typing as T


F = T.TypeVar('F', bound=T.Callable)
G = T.TypeVar('G', bound=T.Callable)

def cache(fn:F=None, folder='.cache') -> F | T.Callable[[G], G]:
    """
    Decorate a function to cache its results. Pyr serialization hashes the function code str + input arguments values. Pickle used to save the results to disk.
    """
    if fn is None:
        return lambda f: cache(f, folder)
    elif isinstance(fn, str):
        return lambda f: cache(f, fn)
    else:
        fn_full_name = get_import_path(fn)
        fn_code = ins.getsource(fn)
        def wrapper(*args, **kwargs):
            h = ''.join({
                ' ': '_', '\n': '_', '\t': '_', '\r': '_', '\\': '_', '/': '_', ':': '_',
                '*': '_', '?': '_', '"': '_', '<': '_', '>': '_', '|': '_',
            }.get(c, c) for c in hash((fn_full_name, fn_code, args, kwargs)))
            file = File(f'{folder}/{fn_full_name}_{h}.pkl')
            if file.path.exists():
                return file.load()
            else:
                result = fn(*args, **kwargs)
                file.save(result)
                return result
        return wrapper


if __name__ == '__main__':

    @cache
    def process_the_thing(x):
        print('Processing the thing...')
        return x * 2

    print(f'{process_the_thing(2) = }')
    print(f'{process_the_thing(2) = }')
