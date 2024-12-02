
import sys
import pathlib as pl
import importlib as imp

def get_import_path(cls_or_fn):
    module = cls_or_fn.__module__
    if module is None or module == str.__class__.__module__:
        return cls_or_fn.__qualname__
    return module + '.' + cls_or_fn.__qualname__

def import_obj_from_path(import_path):
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