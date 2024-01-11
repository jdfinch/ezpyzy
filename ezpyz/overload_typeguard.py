"""
Use decorator @overload for true overloading of functions or methods of the same name.

This version checks if arguments can bind to parameters and each argument matches the parameter's type annotation using `typeguard.check_type` of the `typeguard` package.
"""

try:
    import typeguard
except ImportError:
    raise ImportError('''
    This version of overload requires typeguard to be installed. Install it with:
        pip install typeguard
    ''')
import functools
import inspect
import typing


class Overload:
    def __init__(self, fn):
        self.overloads = [fn]

    def __call__(self, *args, **kwargs):
        for overload in self.overloads:
            try:
                signature = inspect.signature(overload)
                bound = signature.bind(*args, **kwargs)
                for name, arg in bound.arguments.items():
                    param = signature.parameters[name]
                    if param.annotation is not param.empty:
                        if param.default is not param.empty:
                            types = typing.Union[param.annotation, type(param.default), param.default]
                        else:
                            types = param.annotation
                        typeguard.check_type(arg, types)
                return overload(*args, **kwargs)
            except Exception:
                continue
        else:
            name = self.overloads[0].__name__
            message = f'''\n  Signatures of {name} are:\n''' + '\n'.join(
                    f"    {name}{inspect.signature(overload)}"
                    for overload in self.overloads
                ) + f'''\n  But provided args and kwargs do not match:\n    {", ".join([repr(a) for a in args]+[key+"="+repr(value) for key, value in kwargs.items()])}'''
            raise TypeError(message)

    def __get__(self, instance, owner):
        return functools.partial(self.__call__, instance or owner)

    def overload(self, fn):
        self.overloads.append(fn)
        return self


F = typing.TypeVar('F')

def overload(fn: F) -> F:
    context = inspect.currentframe().f_back.f_locals
    existing = context.get(fn.__name__)
    if isinstance(existing, Overload):
        return existing.overload(fn)
    else:
        return Overload(fn)



'''Lol, type checker bamboozled'''
_tmp_overload = typing.overload
setattr(typing, 'overload', overload)
overload = typing.overload
setattr(typing, 'overload', _tmp_overload)





if __name__ == '__main__':

    class Bar:

        @overload
        def foo(self, x: int):
            return x + 1

        @overload
        def foo(self, y: str, z: str = "0"):
            return float(y) + float(z) + 1

        @overload
        def foo(self, x: list[float], c: float = 0):
            return sum(x) + c + 1


    bar = Bar()
    print(f'{bar.foo("3") = }')






