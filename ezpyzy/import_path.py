
import sys
import pathlib as pl
import importlib as imp

def get_import_path(cls_or_fn):
    name = cls_or_fn.__name__
    module = sys.modules[cls_or_fn.__module__]
    file = module.__file__
    cwd = pl.Path.cwd()
    path = pl.Path(file).relative_to(cwd)
    import_path = '.'.join((*path.parts[:-1], path.stem, name))
    return import_path

def import_from_path(import_path):
    module, name = import_path.rsplit('.', 1)
    main_module_path = pl.Path(sys.modules['__main__'].__file__)
    cwd = pl.Path.cwd()
    main_module_path = main_module_path.relative_to(cwd)
    main_module = '.'.join((*main_module_path.parts[:-1], main_module_path.stem))
    if module == main_module:
        module = '__main__'
    if module not in sys.modules:
        sys.modules[module] = imp.import_module(module)
    obj = getattr(sys.modules[module], name)
    return obj