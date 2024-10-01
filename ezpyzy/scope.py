
import inspect as ins


class Scope:

    def __init__(self, frames_back=1, capture_overwritten_vars=True):
        object.__setattr__(self, '__original__', None)
        object.__setattr__(self, '__capture_overwritten__', capture_overwritten_vars)
        object.__setattr__(self, '__frames_back__', frames_back)
        frame = ins.currentframe()
        for i in range(object.__getattribute__(self, '__frames_back__')):
            frame = frame.f_back
        object.__setattr__(self, '__frame__', frame.f_locals)
        object.__setattr__(self, '__captured__', frame.f_locals)

    def __getattr__(self, item):
        return self.__captured__[item]

    def __setattr__(self, key, value):
        self.__frame__[key] = value

    def __getitem__(self, item):
        return self.__captured__[item]

    def __setitem__(self, key, value):
        self.__frame__[key] = value

    def __iter__(self):
        return iter(self.__captured__.items())

    def __len__(self):
        return len(self.__captured__)

    def __contains__(self, item):
        return item in self.__captured__

    def __enter__(self):
        frame = ins.currentframe()
        for i in range(object.__getattribute__(self, '__frames_back__')):
            frame = frame.f_back
        object.__setattr__(self, '__frame__', frame.f_locals)
        object.__setattr__(self, '__original__', frame.f_locals.copy())
        object.__setattr__(self, '__captured__', {})
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        vars = self.__frame__.copy()
        for name, var in vars.items():
            if var is self:
                continue
            if name not in self.__original__:
                self.__captured__[name] = var
            elif self.__capture_overwritten__ and self.__original__[name] is not var:
                self.__captured__[name] = var

    def __str__(self):
        return f"Scope({', '.join(key+': '+str(value) for key, value in self)})"
    __repr__ = __str__