
import sys


globalized_tag = '__globalized__'

def globalize(fn):
    """
    Function to register a function or class in global scope so that it can be pickled or otherwise recognized.
    """
    globalized_fn_name = ''.join((
        globalized_tag,
        ''.join(c if c.isalnum() else '_' for c in fn.__qualname__),
        str(id(fn))))
    def global_fn(*args, **kwargs):
        return fn(*args, **kwargs)
    fn_module = sys.modules[global_fn.__module__]
    if not hasattr(fn_module, globalized_fn_name):
        global_fn.__name__ = global_fn.__qualname__ = globalized_fn_name
        setattr(fn_module, global_fn.__name__, global_fn)
    else:
        global_fn = getattr(fn_module, globalized_fn_name)
    return global_fn