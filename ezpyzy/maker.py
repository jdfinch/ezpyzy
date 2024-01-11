"""
Problem:
Define a function that processes data and saves to target files, but only if the target files are out-of-date with respect to some source files.

Current solution:
Use the caches.cached or Cache.cached methods in cache.py, specifying sources and targets dynamically and receiving None if the targets are out-of-date and need to be recomputed.
"""



from ezpyzy.cache import Cache, caches

import typing as T


F = T.TypeVar('F')

def maker(fn:F=None, **vars_in_or_excluded) -> F:
    ...









import pathlib


def maker(fn=None, *targets, **dependencies):
    if fn is None:
        return lambda fn: maker(fn, *targets, **dependencies)
    targets = [pathlib.Path(target) for target in targets]
    dependencies = {key: pathlib.Path(value) for key, value in dependencies.items()}
    def wrapper(*args, **kwargs):
        for target in targets:
            if not target.exists() or any(
                dependency.stat().st_mtime > target.stat().st_mtime
                for dependency in dependencies.values()
            ):
                fn(*args, **kwargs)
                break
        else:
             return tuple(target.read_text() for target in targets)
    return wrapper

"""
Need a way to have a function whose job is to convert some dependency files into target files, and automagically detects if the target files have been modified after the dependencies to skip work and just load existing targets.

Critically, the targets (paths) might be defined as a function of the dependencies (paths).
"""


import re

def glob_match(pattern, text):
    regex_pattern = pattern.replace('.', r'\.')  # Escape dots
    regex_pattern = regex_pattern.replace('/', r'\/')  # Escape slashes
    regex_pattern = regex_pattern.replace('*', '(.*?)')  # Capture * segments

    match = re.fullmatch(regex_pattern, text)
    if match:
        return match.groups()
    else:
        return None

cases = [
    ['*/bar/*.txt', 'foo/bar/baz.txt'],
    ['*', 'foo/bar/baz.txt'],
    ['*.txt', 'foo/bar/baz.txt'],
    ['*.txt', 'foo/bar/baz.json'],
    ['foo/*.txt', 'foo/bar/baz.txt'],
    ['*/*/*.*', 'foo/bar/baz.txt'],
    ['*/*/*/*/*', 'foo/bar/baz.txt'],
]

for pattern, text in cases:
    print(f'glob_match({pattern}, {text}) = {glob_match(pattern, text)}')






dataproc = ...
DataProc = ...
Data = ...



class MyDataProcessor(DataProc):

    def targets(self, path_dependency_a, path_dependency_b, path_dependency_c):
        path_target_1 = ...
        path_target_2 = ...
        return path_target_1, path_target_2

    def process(self, dependency_a: Data, dependency_b: Data, dependency_c: Data):
        target_1 = ...
        target_2 = ...
        return target_1, target_2

    __call__: ...


mdp = MyDataProcessor()

result_1, result_2 = mdp('path/to/dependency/a', 'path/to/dependency/b', 'path/to/dependency/c')
'''but mdp will know if targets are up-to-date and will load instead of recomputing if so'''




'''
Another way would be:

(dumb, can't preserve type annotation of return values)
'''

@dataproc
def my_data_processor(dependency_a: Data, dependency_b: Data, dependency_c: Data):
    path_target_1 = ...
    path_target_2 = ...
    yield path_target_1, path_target_2
    target_1 = ...
    target_2 = ...
    yield target_1, target_2















