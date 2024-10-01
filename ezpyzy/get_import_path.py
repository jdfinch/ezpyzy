
import sys
import pathlib as pl

def get_import_path(cls_or_fn):
    name = cls_or_fn.__name__
    module = sys.modules[cls_or_fn.__module__]
    file = module.__file__
    cwd = pl.Path.cwd()
    path = pl.Path(file).relative_to(cwd)
    import_path = '.'.join((*path.parts[:-1], path.stem, name))
    return import_path